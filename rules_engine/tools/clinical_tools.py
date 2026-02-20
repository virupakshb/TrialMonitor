"""
Clinical tools for deterministic data checks
These tools fetch and validate clinical trial data
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os


class ClinicalTools:
    """Tools for accessing and validating clinical trial data"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use absolute path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, 'clinical_trial.db')
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database not found at {db_path}")
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========================================================================
    # SUBJECT DATA
    # ========================================================================
    
    def get_subject(self, subject_id: str) -> Optional[Dict[str, Any]]:
        """Get subject basic information"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.*, d.*
            FROM subjects s
            LEFT JOIN demographics d ON s.subject_id = d.subject_id
            WHERE s.subject_id = ?
        """, (subject_id,))
        
        result = cur.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_subject_status(self, subject_id: str) -> str:
        """Get subject study status"""
        subject = self.get_subject(subject_id)
        return subject.get('study_status', 'Unknown') if subject else 'Unknown'
    
    # ========================================================================
    # MEDICAL HISTORY
    # ========================================================================
    
    def check_medical_history(
        self,
        subject_id: str,
        search_terms: List[str],
        status_filter: str = "any"
    ) -> Dict[str, Any]:
        """
        Search medical history for conditions
        
        Args:
            subject_id: Subject ID
            search_terms: List of terms to search for
            status_filter: "ongoing", "resolved", or "any"
            
        Returns:
            {
                "found": bool,
                "matches": [list of matching conditions],
                "evidence": [list of evidence strings]
            }
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        # Build search query
        search_conditions = " OR ".join([
            "LOWER(condition) LIKE ?" for _ in search_terms
        ])
        
        query = f"""
            SELECT condition, diagnosis_date, ongoing, resolution_date,
                   condition_category, condition_notes
            FROM medical_history
            WHERE subject_id = ?
            AND ({search_conditions})
        """
        
        params = [subject_id] + [f"%{term.lower()}%" for term in search_terms]
        
        if status_filter == "ongoing":
            query += " AND ongoing = 1"
        elif status_filter == "resolved":
            query += " AND ongoing = 0"
        
        cur.execute(query, params)
        results = cur.fetchall()
        conn.close()
        
        matches = []
        evidence = []
        
        for row in results:
            row_dict = dict(row)
            matches.append(row_dict)
            
            status_str = "ongoing" if row_dict['ongoing'] else f"resolved {row_dict['resolution_date']}"
            evidence.append(
                f"{row_dict['condition']} (diagnosed {row_dict['diagnosis_date']}, {status_str})"
            )
        
        return {
            "found": len(matches) > 0,
            "matches": matches,
            "evidence": evidence,
            "search_terms": search_terms
        }
    
    # ========================================================================
    # CONCOMITANT MEDICATIONS
    # ========================================================================
    
    def check_conmeds(
        self,
        subject_id: str,
        medication_names: List[str] = None,
        medication_classes: List[str] = None
    ) -> Dict[str, Any]:
        """Check concomitant medications"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = ["subject_id = ?", "ongoing = 1"]
        params = [subject_id]
        
        if medication_names:
            name_conditions = " OR ".join(
                ["LOWER(medication_name) LIKE ?" for _ in medication_names]
            )
            conditions.append(f"({name_conditions})")
            params.extend([f"%{name.lower()}%" for name in medication_names])
        
        if medication_classes:
            class_conditions = " OR ".join(
                ["LOWER(medication_class) LIKE ?" for _ in medication_classes]
            )
            conditions.append(f"({class_conditions})")
            params.extend([f"%{mc.lower()}%" for mc in medication_classes])
        
        query = f"""
            SELECT medication_name, dose, dose_unit, frequency, route,
                   start_date, end_date, ongoing, medication_class, indication
            FROM concomitant_medications
            WHERE {' AND '.join(conditions)}
        """
        
        cur.execute(query, params)
        results = cur.fetchall()
        conn.close()
        
        medications = []
        evidence = []
        
        for row in results:
            row_dict = dict(row)
            medications.append(row_dict)
            
            # dose field may already contain the unit (e.g. "4 mg"), so only
            # append dose_unit if it isn't already present in the dose string
            dose_str = str(row_dict['dose']) if row_dict['dose'] is not None else ""
            unit_str = str(row_dict['dose_unit']) if row_dict['dose_unit'] else ""
            if unit_str and unit_str not in dose_str:
                dose_info = f"{dose_str} {unit_str}".strip()
            else:
                dose_info = dose_str
            ongoing_status = (
                "ONGOING (no end date)"
                if row_dict.get('ongoing') == 1 and not row_dict.get('end_date')
                else (f"ended {row_dict.get('end_date')}" if row_dict.get('end_date') else "status unknown")
            )
            evidence.append(
                f"{row_dict['medication_name']} {dose_info} {row_dict['frequency']} "
                f"(started {row_dict['start_date']}, {ongoing_status}, indication: {row_dict.get('indication', 'not specified')})"
            )
        
        return {
            "found": len(medications) > 0,
            "medications": medications,
            "evidence": evidence
        }
    
    # ========================================================================
    # LABORATORY RESULTS
    # ========================================================================
    
    def check_lab_threshold(
        self,
        subject_id: str,
        test_name: str,
        operator: str,
        threshold: float,
        timepoint: str = "latest"
    ) -> Dict[str, Any]:
        """
        Check if lab value meets threshold
        
        Args:
            subject_id: Subject ID
            test_name: Lab test name
            operator: ">=", ">", "<=", "<", "=="
            threshold: Threshold value
            timepoint: "latest", "screening", or "baseline"
            
        Returns:
            {
                "meets_criterion": bool,
                "actual_value": float,
                "threshold": float,
                "test_date": date,
                "evidence": str
            }
        """
        conn = self._get_connection()
        cur = conn.cursor()

        # QTcF lives in ecg_results, not laboratory_results — handle specially
        if test_name.upper() in ("QTCF", "QTC", "QT"):
            ecg_col = "qtcf_interval" if test_name.upper() == "QTCF" else "qtc_interval"

            if timepoint == "screening":
                # Use the earliest ECG (closest to screening date)
                ecg_query = f"""
                    SELECT {ecg_col} AS test_value, ecg_date AS collection_date,
                           interpretation, abnormal
                    FROM ecg_results
                    WHERE subject_id = ? AND {ecg_col} IS NOT NULL
                    ORDER BY ecg_date ASC
                    LIMIT 1
                """
            else:
                ecg_query = f"""
                    SELECT {ecg_col} AS test_value, ecg_date AS collection_date,
                           interpretation, abnormal
                    FROM ecg_results
                    WHERE subject_id = ? AND {ecg_col} IS NOT NULL
                    ORDER BY ecg_date DESC
                    LIMIT 1
                """

            cur.execute(ecg_query, (subject_id,))
            result = cur.fetchone()
            conn.close()

            if not result:
                return {
                    "meets_criterion": None,
                    "actual_value": None,
                    "evidence": f"No {test_name} result found in ECG data",
                    "missing_data": True
                }

            result_dict = dict(result)
            value = result_dict["test_value"]
            date = result_dict["collection_date"]
            ops = {
                ">=": lambda a, b: a >= b,
                ">": lambda a, b: a > b,
                "<=": lambda a, b: a <= b,
                "<": lambda a, b: a < b,
                "==": lambda a, b: a == b
            }
            meets = ops[operator](value, threshold) if value is not None else None
            return {
                "meets_criterion": meets,
                "actual_value": value,
                "threshold": threshold,
                "operator": operator,
                "unit": "msec",
                "test_date": date,
                "interpretation": result_dict.get("interpretation", ""),
                "evidence": (
                    f"{test_name}: {value} msec {operator} {threshold} msec "
                    f"(ECG date: {date}, {result_dict.get('interpretation', '')}) "
                    f"-> {'VIOLATION' if meets else 'PASS'}"
                ),
                "missing_data": False
            }

        query = """
            SELECT test_value, test_unit, collection_date, normal_range_lower, normal_range_upper
            FROM laboratory_results
            WHERE subject_id = ? AND test_name = ?
            ORDER BY collection_date DESC
            LIMIT 1
        """

        cur.execute(query, (subject_id, test_name))
        result = cur.fetchone()
        conn.close()

        if not result:
            return {
                "meets_criterion": None,
                "actual_value": None,
                "evidence": f"No {test_name} result found",
                "missing_data": True
            }
        
        result_dict = dict(result)
        value = result_dict['test_value']
        unit = result_dict['test_unit']
        date = result_dict['collection_date']
        
        # Operator evaluation
        ops = {
            ">=": lambda a, b: a >= b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            "<": lambda a, b: a < b,
            "==": lambda a, b: a == b
        }
        
        meets = ops[operator](value, threshold) if value is not None else None
        
        return {
            "meets_criterion": meets,
            "actual_value": value,
            "threshold": threshold,
            "operator": operator,
            "unit": unit,
            "test_date": date,
            "normal_range_lower": result_dict['normal_range_lower'],
            "normal_range_upper": result_dict['normal_range_upper'],
            "evidence": f"{test_name}: {value} {unit} {operator} {threshold} -> {'PASS' if meets else 'FAIL'}",
            "missing_data": False
        }
    
    def get_labs_for_subject(
        self,
        subject_id: str,
        test_names: List[str] = None,
        timeframe_days: int = None
    ) -> List[Dict[str, Any]]:
        """Get lab results for subject"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT *
            FROM laboratory_results
            WHERE subject_id = ?
        """
        params = [subject_id]
        
        if test_names:
            placeholders = ','.join(['?' for _ in test_names])
            query += f" AND test_name IN ({placeholders})"
            params.extend(test_names)
        
        if timeframe_days:
            cutoff_date = (datetime.now() - timedelta(days=timeframe_days)).date().isoformat()
            query += " AND collection_date >= ?"
            params.append(cutoff_date)
        
        query += " ORDER BY collection_date DESC"
        
        cur.execute(query, params)
        results = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    # ========================================================================
    # ADVERSE EVENTS
    # ========================================================================
    
    def get_adverse_events(
        self,
        subject_id: str,
        seriousness: str = None,
        ongoing: bool = None
    ) -> List[Dict[str, Any]]:
        """Get adverse events for subject"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        query = "SELECT * FROM adverse_events WHERE subject_id = ?"
        params = [subject_id]
        
        if seriousness:
            query += " AND seriousness = ?"
            params.append(seriousness)
        
        if ongoing is not None:
            query += " AND ongoing = ?"
            params.append(1 if ongoing else 0)
        
        query += " ORDER BY onset_date DESC"
        
        cur.execute(query, params)
        results = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    # ========================================================================
    # VISITS
    # ========================================================================
    
    def get_visit(self, subject_id: str, visit_number: int) -> Optional[Dict[str, Any]]:
        """Get specific visit"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT *
            FROM visits
            WHERE subject_id = ? AND visit_number = ?
        """, (subject_id, visit_number))
        
        result = cur.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_visits_for_subject(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get all visits for subject"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT *
            FROM visits
            WHERE subject_id = ?
            ORDER BY visit_number
        """, (subject_id,))
        
        results = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    # ========================================================================
    # ECG
    # ========================================================================
    
    def get_ecg_results(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get ECG results"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT *
            FROM ecg_results
            WHERE subject_id = ?
            ORDER BY ecg_date DESC
        """, (subject_id,))
        
        results = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    # ========================================================================
    # TUMOR ASSESSMENTS
    # ========================================================================
    
    def get_tumor_assessments(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get tumor assessments"""
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM tumor_assessments
            WHERE subject_id = ?
            ORDER BY assessment_date
        """, (subject_id,))

        results = cur.fetchall()
        conn.close()

        return [dict(row) for row in results]

    # ========================================================================
    # VISIT WINDOW CHECK
    # ========================================================================

    def check_visit_windows(self, subject_id: str) -> Dict[str, Any]:
        """
        Check whether any completed visits fall outside the protocol window.

        Protocol windows per NVX-1218.22:
          - Treatment visits (visit_number 3-10): +/- 3 days
          - Follow-up visit (visit_number 11):    +/- 7 days

        Returns:
            {
                "out_of_window": [...],
                "total_visits_checked": int,
                "all_within_window": bool
            }
        """
        from datetime import date as dt_date

        visits = self.get_visits_for_subject(subject_id)
        out_of_window = []

        for v in visits:
            if not v.get('visit_completed'):
                continue
            scheduled_str = v.get('scheduled_date')
            actual_str = v.get('actual_date')
            if not scheduled_str or not actual_str:
                continue

            try:
                scheduled = dt_date.fromisoformat(str(scheduled_str))
                actual = dt_date.fromisoformat(str(actual_str))
            except ValueError:
                continue

            visit_number = v.get('visit_number', 0)
            window_days = 7 if visit_number == 11 else 3

            days_off = (actual - scheduled).days
            if abs(days_off) > window_days:
                out_of_window.append({
                    "visit_name": v.get('visit_name', f"Visit {visit_number}"),
                    "visit_number": visit_number,
                    "scheduled_date": str(scheduled_str),
                    "actual_date": str(actual_str),
                    "days_off": days_off,
                    "window_days": window_days,
                    "description": (
                        f"{v.get('visit_name', 'Visit')} (#{visit_number}): "
                        f"scheduled {scheduled_str}, actual {actual_str} "
                        f"({'early' if days_off < 0 else 'late'} by {abs(days_off)} days, "
                        f"window is +/-{window_days} days) -> OUTSIDE WINDOW"
                    )
                })

        return {
            "out_of_window": out_of_window,
            "total_visits_checked": len([v for v in visits if v.get('visit_completed')]),
            "all_within_window": len(out_of_window) == 0
        }

    # ========================================================================
    # DEMOGRAPHICS HELPER
    # ========================================================================

    def get_demographics(self, subject_id: str) -> Optional[Dict[str, Any]]:
        """Get demographics record for subject"""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM demographics WHERE subject_id = ?",
            (subject_id,)
        )
        result = cur.fetchone()
        conn.close()
        return dict(result) if result else None
