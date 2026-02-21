"""
Generate synthetic TMF (Trial Master File) PDF documents for all 5 sites.
Uses fpdf2. Run once to populate tmf_documents/ folder.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ─────────────────────────────────────────────────────────────────────────────
# Unicode sanitisation (same as generate_pdf.py)
# ─────────────────────────────────────────────────────────────────────────────
UNICODE_MAP = {
    '\u2014': '--', '\u2013': '-', '\u2018': "'", '\u2019': "'",
    '\u201c': '"', '\u201d': '"', '\u2022': '-', '\u00b7': '-',
    '\u00a0': ' ', '\u2026': '...', '\u00ae': '(R)', '\u00a9': '(C)',
    '\u2122': '(TM)', '\u00b0': ' deg', '\u00b1': '+/-',
    '\u00e9': 'e', '\u00e8': 'e', '\u00ea': 'e', '\u00eb': 'e',
    '\u00e0': 'a', '\u00e1': 'a', '\u00e2': 'a', '\u00e4': 'a',
    '\u00fc': 'u', '\u00f6': 'o', '\u00e7': 'c', '\u00df': 'ss',
}

def sanitize(text):
    if text is None:
        return ''
    for char, replacement in UNICODE_MAP.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', errors='replace').decode('latin-1')


# ─────────────────────────────────────────────────────────────────────────────
# Base PDF class
# ─────────────────────────────────────────────────────────────────────────────
class TmfPDF(FPDF):
    def __init__(self, site_name='', doc_title=''):
        super().__init__()
        self.site_name = site_name
        self.doc_title = doc_title

    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.rect(0, 0, 210, 14, 'F')
        self.set_y(4)
        self.cell(0, 6, sanitize(f'NVX-1218.22 -- NovaPlex-450 -- Trial Master File'), align='C',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.set_font('Helvetica', '', 7)
        self.set_y(14)
        self.cell(0, 4, sanitize(f'{self.site_name}  |  {self.doc_title}'), align='C',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, sanitize(f'CONFIDENTIAL -- For regulatory purposes only -- Page {self.page_no()}'),
                  align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(237, 242, 255)
        self.set_text_color(30, 58, 95)
        self.cell(0, 8, sanitize(title), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def body_text(self, text, size=10):
        self.set_font('Helvetica', '', size)
        self.multi_cell(0, 6, sanitize(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def field_row(self, label, value, label_w=60):
        self.set_font('Helvetica', 'B', 10)
        self.cell(label_w, 7, sanitize(label + ':'), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font('Helvetica', '', 10)
        self.cell(0, 7, sanitize(str(value)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def table_header(self, cols, widths):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        for col, w in zip(cols, widths):
            self.cell(w, 7, sanitize(col), border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.ln()
        self.set_text_color(0, 0, 0)

    def table_row(self, vals, widths, fill=False):
        self.set_font('Helvetica', '', 9)
        if fill:
            self.set_fill_color(248, 250, 252)
        for val, w in zip(vals, widths):
            self.cell(w, 7, sanitize(str(val)), border=1, fill=fill, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.ln()


# ─────────────────────────────────────────────────────────────────────────────
# Site definitions
# ─────────────────────────────────────────────────────────────────────────────
SITES = {
    '101': {
        'name': 'Memorial Cancer Center',
        'city': 'Boston, MA, USA',
        'pi': 'Dr. Emily Chen',
        'pi_credentials': 'MD, PhD -- Medical Oncology',
        'pi_institution': 'Memorial Cancer Center, Harvard Medical School Affiliate',
        'coordinator': 'Jessica Martinez',
        'coord_credentials': 'RN, BSN, CCRC',
        'lab': 'Boston Clinical Reference Laboratory',
        'irb': 'New England IRB (NEIRB)',
        'irb_num': 'NEIRB-2024-0112',
        'activation': '2024-01-15',
    },
    '102': {
        'name': 'London Oncology Institute',
        'city': 'London, United Kingdom',
        'pi': 'Dr. James Harrison',
        'pi_credentials': 'MBBS, PhD, FRCP -- Medical Oncology',
        'pi_institution': 'London Oncology Institute, University College London',
        'coordinator': 'Sophie Williams',
        'coord_credentials': 'RN, MSc, CCRC',
        'lab': 'UK Bioanalytical Services Ltd',
        'irb': 'London Multi-Centre Research Ethics Committee',
        'irb_num': 'LMREC-2024-0089',
        'activation': '2024-02-01',
    },
    '103': {
        'name': 'Toronto Research Hospital',
        'city': 'Toronto, ON, Canada',
        'pi': 'Dr. Priya Sharma',
        'pi_credentials': 'MD, FRCPC -- Hematology/Oncology',
        'pi_institution': 'Toronto Research Hospital, University of Toronto',
        'coordinator': 'Michael Wong',
        'coord_credentials': 'RN, BScN, CCRP',
        'lab': 'LifeLabs Medical Laboratory Services',
        'irb': 'Toronto Academic Health Sciences Network REB',
        'irb_num': 'TAHSN-REB-2024-0203',
        'activation': '2024-01-20',
    },
    '104': {
        'name': 'Sydney Cancer Center',
        'city': 'Sydney, NSW, Australia',
        'pi': "Dr. David O'Connor",
        'pi_credentials': 'MBBS, PhD, FRACP -- Medical Oncology',
        'pi_institution': 'Sydney Cancer Center, University of Sydney',
        'coordinator': 'Emma Thompson',
        'coord_credentials': 'RN, BN, CCRC',
        'lab': 'Sonic Healthcare -- Sydney Reference Laboratories',
        'irb': 'Sydney Local Health District HREC',
        'irb_num': 'SLHD-HREC-2024-0156',
        'activation': '2024-03-01',
    },
    '105': {
        'name': 'Singapore Medical Research',
        'city': 'Singapore',
        'pi': 'Dr. Wei Zhang',
        'pi_credentials': 'MBBS, PhD, FAMS -- Medical Oncology',
        'pi_institution': 'Singapore Medical Research Centre, National University of Singapore',
        'coordinator': 'Lisa Tan',
        'coord_credentials': 'RN, BSc, CRC',
        'lab': 'Parkway Laboratory Services Ltd',
        'irb': 'National Healthcare Group Domain Specific Review Board',
        'irb_num': 'NHG-DSRB-2024-0301',
        'activation': '2024-04-01',
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Document generators
# ─────────────────────────────────────────────────────────────────────────────

def gen_delegation_log(site_id, s, out_path):
    pdf = TmfPDF(site_name=s['name'], doc_title='Site Delegation Log v1.0')
    pdf.add_page()
    pdf.section_title('SITE DELEGATION LOG')
    pdf.field_row('Protocol', 'NVX-1218.22 -- NovaPlex-450 in Advanced NSCLC')
    pdf.field_row('Site', f"{site_id} -- {s['name']}, {s['city']}")
    pdf.field_row('Principal Investigator', s['pi'])
    pdf.field_row('Version', 'v1.0')
    pdf.field_row('Effective Date', s['activation'])
    pdf.ln(4)
    pdf.body_text(
        'The Principal Investigator delegates the following study-related tasks to qualified site staff. '
        'All delegated staff have received appropriate training and are qualified to perform the tasks listed.'
    )
    pdf.ln(2)

    cols = ['Staff Name', 'Role', 'Qualifications', 'Delegated Tasks', 'From', 'To', 'Init.']
    widths = [38, 28, 28, 50, 18, 18, 10]
    pdf.table_header(cols, widths)

    rows = [
        [s['pi'], 'Principal Investigator', s['pi_credentials'],
         'All study activities, overall responsibility', s['activation'], 'Ongoing', 'EC'],
        [s['coordinator'], 'Study Coordinator', s['coord_credentials'],
         'Subject consent, data entry, query resolution, drug dispensing', s['activation'], 'Ongoing', 'JM'],
        [f"Dr. Sub-I ({s['name'][:10]})", 'Sub-Investigator', 'MD, Medical Oncology',
         'Subject assessment, AE evaluation, dose decisions', s['activation'], 'Ongoing', 'SI'],
        ['Research Nurse', 'Research Nurse', 'RN, BSc',
         'Sample collection, vital signs, ECG, study procedures', s['activation'], 'Ongoing', 'RN'],
        ['Data Manager', 'Clinical Data Manager', 'BSc, CCDM',
         'EDC data entry review, query management', s['activation'], 'Ongoing', 'DM'],
    ]
    for i, row in enumerate(rows):
        pdf.table_row(row, widths, fill=(i % 2 == 0))

    pdf.ln(6)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 7, 'Principal Investigator Signature:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 0.5, '', border='B')
    pdf.cell(10, 7, '')
    pdf.cell(50, 0.5, '', border='B')
    pdf.ln(4)
    pdf.cell(80, 6, sanitize(s['pi']), new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(10, 6, '')
    pdf.cell(50, 6, s['activation'])
    pdf.ln()
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(80, 5, 'Signature', new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(10, 5, '')
    pdf.cell(50, 5, 'Date')
    pdf.output(out_path)


def gen_irb_approval(site_id, s, out_path, amendment=False):
    title = 'IRB Amendment Approval v2.1' if amendment else 'IRB Initial Approval'
    pdf = TmfPDF(site_name=s['name'], doc_title=title)
    pdf.add_page()
    pdf.section_title('ETHICS COMMITTEE / IRB APPROVAL LETTER')
    pdf.field_row('From', s['irb'])
    pdf.field_row('To', s['pi'])
    pdf.field_row('Reference Number', s['irb_num'] + ('-AMD-001' if amendment else ''))
    pdf.field_row('Date', '2024-11-20' if amendment else s['activation'])
    pdf.field_row('Protocol', 'NVX-1218.22 -- NovaPlex-450 in Advanced NSCLC')
    pdf.field_row('Amendment', 'Protocol Amendment v2.1' if amendment else 'N/A -- Initial Approval')
    pdf.ln(4)

    if amendment:
        pdf.section_title('Amendment Approval')
        pdf.body_text(
            'Dear ' + s['pi'] + ',\n\n'
            'The ' + s['irb'] + ' has reviewed and approved Protocol Amendment v2.1 '
            'dated 2024-11-01 for the above-referenced study. The amendment includes:\n\n'
            '1. Revised inclusion/exclusion criteria (Section 4.2)\n'
            '2. Updated Informed Consent Form (ICF v2.1) -- all active subjects must be re-consented\n'
            '3. Modified visit schedule -- Week 12 visit extended from Day 84 +/-3 to Day 84 +/-7\n\n'
            'IMPORTANT: All currently enrolled subjects must provide updated consent using ICF v2.1 '
            'prior to their next scheduled study visit. Please ensure all site staff are trained on '
            'the protocol changes before implementing.'
        )
    else:
        pdf.section_title('Initial Approval')
        pdf.body_text(
            'Dear ' + s['pi'] + ',\n\n'
            'The ' + s['irb'] + ' is pleased to confirm approval of the above-referenced '
            'clinical study at your institution. This approval is effective from ' + s['activation'] + ' '
            'and is valid for 12 months.\n\n'
            'This approval covers:\n'
            '- Protocol Version 1.0 (dated 2023-12-01)\n'
            '- Informed Consent Form Version 1.0 (dated 2023-12-01)\n'
            '- Patient recruitment materials as submitted\n\n'
            'Conditions of approval:\n'
            '1. Any protocol amendments must be submitted for review prior to implementation\n'
            '2. Annual progress reports must be submitted\n'
            '3. All serious adverse events must be reported within 7 days\n'
            '4. The study must be conducted in accordance with ICH GCP E6(R2) guidelines'
        )

    pdf.ln(4)
    pdf.section_title('Approval Details')
    pdf.field_row('Status', 'APPROVED')
    pdf.field_row('Approval Date', '2024-11-20' if amendment else s['activation'])
    pdf.field_row('Expiry Date', '2025-11-20' if amendment else '2025-01-14')
    pdf.field_row('Renewal Required', 'Yes -- submit renewal 60 days before expiry')

    pdf.ln(6)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 7, 'Chairperson Signature:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.cell(80, 0.5, '', border='B')
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(80, 5, 'IRB Chairperson')
    pdf.output(out_path)


def gen_icf(site_id, s, out_path):
    pdf = TmfPDF(site_name=s['name'], doc_title='Informed Consent Form v2.1')
    pdf.add_page()
    pdf.section_title('INFORMED CONSENT FORM')
    pdf.field_row('Study Title', 'A Phase III Study of NovaPlex-450 in Advanced NSCLC')
    pdf.field_row('Protocol Number', 'NVX-1218.22')
    pdf.field_row('Sponsor', 'NexaVance Therapeutics Inc.')
    pdf.field_row('Principal Investigator', s['pi'])
    pdf.field_row('Site', f"{s['name']}, {s['city']}")
    pdf.field_row('ICF Version', 'v2.1')
    pdf.field_row('Version Date', '2024-11-15')
    pdf.ln(4)

    sections = [
        ('Purpose of the Study',
         'You are being asked to take part in a research study. The purpose of this study is to evaluate '
         'the safety and effectiveness of NovaPlex-450, an investigational drug, compared to standard '
         'chemotherapy in patients with advanced non-small cell lung cancer (NSCLC) whose cancer has '
         'spread and who have not received prior chemotherapy for advanced disease.'),
        ('Study Procedures',
         'If you agree to take part, you will be randomly assigned to receive either NovaPlex-450 or '
         'standard chemotherapy. You will receive study treatment in 21-day cycles. You will attend '
         'clinic visits approximately every 3 weeks for the first 6 months, then every 6 weeks. '
         'Blood tests, tumour assessments (CT scans), and questionnaires will be performed at each visit.'),
        ('Risks and Discomforts',
         'NovaPlex-450 may cause side effects including: nausea, fatigue, decreased blood cell counts, '
         'immune-related reactions, and rarely, more serious effects on the heart, lungs, or liver. '
         'Blood draws may cause bruising. CT scans involve low-level radiation exposure.'),
        ('Benefits',
         'You may benefit from study participation if NovaPlex-450 is effective. However, there is no '
         'guarantee of benefit. Your participation will contribute to scientific knowledge that may '
         'benefit future patients.'),
        ('Voluntary Participation',
         'Your participation is completely voluntary. You may withdraw at any time without penalty or '
         'loss of benefits to which you are otherwise entitled. Your medical care will not be affected '
         'if you choose not to participate or if you withdraw.'),
        ('Confidentiality',
         'Your personal information will be kept strictly confidential. Study data will be identified '
         'only by a subject code. Your records may be inspected by regulatory authorities and the '
         'sponsor for verification purposes, but your identity will remain confidential.'),
    ]

    for title, text in sections:
        pdf.section_title(title)
        pdf.body_text(text)

    pdf.ln(4)
    pdf.section_title('Consent Signature')
    pdf.body_text(
        'I have read and understood the information in this consent form. I have had the opportunity '
        'to ask questions and all my questions have been answered to my satisfaction. I voluntarily '
        'agree to participate in this study.'
    )
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 10)
    for label_pair in [('Subject Name (Print)', 'Subject Signature'), ('Date', 'Witness Signature')]:
        pdf.cell(90, 0.5, '', border='B', new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(10, 7, '')
        pdf.cell(80, 0.5, '', border='B')
        pdf.ln(5)
        pdf.cell(90, 5, label_pair[0], new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(10, 5, '')
        pdf.cell(80, 5, label_pair[1])
        pdf.ln(8)
    pdf.output(out_path)


def gen_pi_cv(site_id, s, out_path):
    pdf = TmfPDF(site_name=s['name'], doc_title=f"Investigator CV -- {s['pi']}")
    pdf.add_page()
    pdf.section_title('CURRICULUM VITAE -- PRINCIPAL INVESTIGATOR')
    pdf.field_row('Name', s['pi'])
    pdf.field_row('Credentials', s['pi_credentials'])
    pdf.field_row('Institution', s['pi_institution'])
    pdf.field_row('Role in Study', 'Principal Investigator -- NVX-1218.22')
    pdf.field_row('CV Date', '2024-03-01')
    pdf.ln(4)

    pdf.section_title('Education & Training')
    edu_rows = [
        ['MD', 'Medicine', 'University (Local)', '1998-2004'],
        ['PhD', 'Oncology', 'Graduate Institute', '2004-2008'],
        ['Residency', 'Internal Medicine', 'Teaching Hospital', '2008-2011'],
        ['Fellowship', 'Medical Oncology', 'Cancer Center', '2011-2013'],
    ]
    pdf.table_header(['Degree', 'Field', 'Institution', 'Year'], [30, 50, 70, 30])
    for i, row in enumerate(edu_rows):
        pdf.table_row(row, [30, 50, 70, 30], fill=(i % 2 == 0))

    pdf.ln(4)
    pdf.section_title('Current Appointments')
    pdf.body_text(f"Principal Investigator and Head of Medical Oncology, {s['name']} (2013-present)")
    pdf.body_text(f"Associate Professor, Oncology, affiliated university (2015-present)")

    pdf.ln(2)
    pdf.section_title('GCP Training')
    pdf.field_row('Last GCP Training', '10 February 2024')
    pdf.field_row('Certificate Valid Until', '10 February 2026')
    pdf.field_row('Training Provider', 'Transcelerate BioPharma / CITI Program')

    pdf.ln(2)
    pdf.section_title('Relevant Clinical Trial Experience')
    pdf.body_text(
        'Principal Investigator on 12 Phase I-III oncology trials over 10 years, '
        'including 4 studies in NSCLC. Co-investigator on 6 additional studies. '
        'Enrolled >150 subjects across oncology trials. No serious protocol deviations '
        'in prior studies. Familiar with ICH GCP E6(R2) requirements.'
    )

    pdf.ln(2)
    pdf.section_title('Publications (Selected)')
    pubs = [
        f"{s['pi'].split('.')[1].strip()} et al. (2022). Novel immunotherapy approaches in advanced NSCLC. J Clin Oncol. 40(15):1623-1634.",
        f"{s['pi'].split('.')[1].strip()} et al. (2020). Real-world outcomes in EGFR-mutated NSCLC. Lung Cancer. 142:45-52.",
        f"{s['pi'].split('.')[1].strip()} et al. (2019). Biomarker-driven patient selection in oncology trials. Ann Oncol. 30(6):987-994.",
    ]
    for pub in pubs:
        pdf.body_text(f"- {pub}", size=9)

    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 7, 'I certify that the information in this CV is current and accurate:',
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.cell(80, 0.5, '', border='B')
    pdf.cell(20, 7, '')
    pdf.cell(50, 0.5, '', border='B')
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(80, 5, sanitize(s['pi']), new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(20, 5, '')
    pdf.cell(50, 5, '2024-03-01')
    pdf.output(out_path)


def gen_gcp_cert(site_id, s, out_path, person_type='pi'):
    name = s['pi'] if person_type == 'pi' else s['coordinator']
    cred = s['pi_credentials'] if person_type == 'pi' else s['coord_credentials']
    date = '2024-02-10' if person_type == 'pi' else '2024-01-20'
    expiry = '2026-02-10' if person_type == 'pi' else '2026-01-20'
    title = f"GCP Training Certificate -- {name}"

    pdf = TmfPDF(site_name=s['name'], doc_title=title)
    pdf.add_page()

    # Certificate header
    pdf.set_fill_color(30, 58, 95)
    pdf.rect(10, 25, 190, 20, 'F')
    pdf.set_y(30)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, 'CERTIFICATE OF TRAINING COMPLETION', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'ICH Good Clinical Practice (GCP) E6(R2)', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, 'This certifies that', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 10, sanitize(name), align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, sanitize(cred), align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, 'has successfully completed the required training in', align='C',
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'ICH E6(R2) Good Clinical Practice Guidelines', align='C',
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'as required by FDA 21 CFR Parts 312 and 812, and EMA GCP Directive', align='C',
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    pdf.section_title('Certificate Details')
    pdf.field_row('Training Provider', 'CITI Program / Transcelerate BioPharma Initiative')
    pdf.field_row('Course Completed', 'Good Clinical Practice -- Investigators and Key Research Staff')
    pdf.field_row('Completion Date', date)
    pdf.field_row('Certificate Valid Until', expiry)
    pdf.field_row('Certificate ID', f"GCP-{site_id}-{person_type.upper()}-2024-{site_id}001")
    pdf.field_row('Score Achieved', '94% (Pass threshold: 80%)')

    pdf.ln(8)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5,
             'This certificate is valid for 2 years from date of completion. Renewal is required '
             'before expiry to maintain eligibility to conduct GCP-regulated clinical research.',
             align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(out_path)


def gen_lab_cert(site_id, s, out_path):
    pdf = TmfPDF(site_name=s['name'], doc_title='Central Laboratory Certification')
    pdf.add_page()
    pdf.section_title('CENTRAL LABORATORY ACCREDITATION CERTIFICATE')
    pdf.field_row('Laboratory', s['lab'])
    pdf.field_row('Site', f"{site_id} -- {s['name']}, {s['city']}")
    pdf.field_row('Protocol', 'NVX-1218.22')
    pdf.field_row('Accreditation Body', 'CAP / ISO 15189 / UKAS')
    pdf.field_row('Certificate Date', '2024-06-01')
    pdf.field_row('Valid Until', '2025-06-01')
    pdf.ln(4)

    pdf.section_title('Certified Tests')
    cols = ['Test Category', 'Tests Included', 'Method', 'Accredited']
    widths = [40, 75, 45, 30]
    pdf.table_header(cols, widths)
    rows = [
        ['Haematology', 'CBC, WBC differential, Platelets', 'Automated analyser', 'Yes'],
        ['Chemistry', 'LFTs (ALT, AST, ALP, Bili), Creatinine, eGFR, Glucose', 'Photometric', 'Yes'],
        ['Coagulation', 'PT, APTT, INR', 'Optical clot detection', 'Yes'],
        ['Immunology', 'ANA, anti-dsDNA, CRP, ESR', 'ELISA / nephelometry', 'Yes'],
        ['Endocrine', 'TSH, Free T4, cortisol', 'ECLIA', 'Yes'],
        ['Urinalysis', 'Dipstick, microscopy', 'Automated', 'Yes'],
    ]
    for i, row in enumerate(rows):
        pdf.table_row(row, widths, fill=(i % 2 == 0))

    pdf.ln(4)
    pdf.section_title('Normal Ranges (Selected -- NVX-1218.22 Protocol)')
    pdf.field_row('ALT', '7-56 U/L (males), 7-45 U/L (females)')
    pdf.field_row('AST', '10-40 U/L')
    pdf.field_row('Creatinine', '62-106 umol/L (males), 44-80 umol/L (females)')
    pdf.field_row('Haemoglobin', '130-175 g/L (males), 120-160 g/L (females)')
    pdf.field_row('Platelets', '150-400 x10^9/L')
    pdf.field_row('Neutrophils', '1.8-7.5 x10^9/L')

    pdf.ln(4)
    pdf.section_title('Laboratory Director')
    pdf.field_row('Director', f"Dr. Lab Director -- {s['lab']}")
    pdf.field_row('Qualifications', 'PhD, FIBMS, FRCPath')
    pdf.ln(6)
    pdf.cell(80, 0.5, '', border='B')
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(80, 5, 'Laboratory Director Signature')
    pdf.output(out_path)


def gen_protocol_synopsis(out_path):
    pdf = TmfPDF(site_name='All Sites', doc_title='Protocol Synopsis v3.0')
    pdf.add_page()
    pdf.section_title('PROTOCOL SYNOPSIS')
    pdf.field_row('Protocol Number', 'NVX-1218.22')
    pdf.field_row('Protocol Title', 'A Phase III, Randomised, Double-Blind Study of NovaPlex-450')
    pdf.field_row('IND Number', 'IND-145892')
    pdf.field_row('Sponsor', 'NexaVance Therapeutics Inc., Cambridge, MA, USA')
    pdf.field_row('Phase', 'Phase III')
    pdf.field_row('Indication', 'Advanced Non-Small Cell Lung Cancer (NSCLC)')
    pdf.field_row('Protocol Version', 'v3.0 (incorporating Amendment v2.1)')
    pdf.field_row('Protocol Date', '2024-11-01')
    pdf.ln(4)

    pdf.section_title('Primary Objective')
    pdf.body_text(
        'To compare progression-free survival (PFS) of NovaPlex-450 plus best supportive care '
        'versus platinum-based doublet chemotherapy in treatment-naive patients with advanced NSCLC '
        '(Stage IIIB/IV) without known actionable driver mutations.'
    )

    pdf.section_title('Primary Endpoint')
    pdf.body_text('Progression-Free Survival (PFS) assessed by blinded independent central review (BICR) per RECIST 1.1.')

    pdf.section_title('Key Inclusion Criteria')
    criteria = [
        'Age >= 18 years',
        'Histologically confirmed advanced NSCLC (Stage IIIB/IV)',
        'No prior systemic therapy for advanced/metastatic disease',
        'ECOG Performance Status 0-1',
        'Adequate organ function (haematology, hepatic, renal)',
        'No known EGFR/ALK/ROS1 mutations or rearrangements',
        'Written informed consent obtained prior to any study procedures',
    ]
    for c in criteria:
        pdf.body_text(f"- {c}", size=9)

    pdf.section_title('Key Exclusion Criteria')
    excl = [
        'Prior immunotherapy or checkpoint inhibitor therapy',
        'Active autoimmune disease requiring systemic treatment within 2 years',
        'Symptomatic brain metastases (stable, treated metastases permitted)',
        'Active cardiac conditions: NYHA Class III/IV heart failure, unstable angina',
        'QTc > 480ms on screening ECG',
        'Known active hepatitis B or C infection',
        'Pregnancy or breastfeeding',
    ]
    for e in excl:
        pdf.body_text(f"- {e}", size=9)

    pdf.section_title('Study Design')
    pdf.body_text(
        'Randomisation 1:1 (NovaPlex-450 vs chemotherapy). Stratification by ECOG PS (0 vs 1), '
        'histology (squamous vs non-squamous), and geographic region. '
        'Treatment continues until disease progression, unacceptable toxicity, or withdrawal of consent. '
        'Tumour assessments every 6 weeks for first 12 months, then every 12 weeks.'
    )

    pdf.section_title('Dosing')
    pdf.field_row('NovaPlex-450', '450mg IV over 60 minutes, Day 1 of each 21-day cycle')
    pdf.field_row('Comparator', 'Carboplatin AUC5 + Pemetrexed 500mg/m2 IV, Day 1 of each 21-day cycle (non-squamous) OR Carboplatin AUC5 + Paclitaxel 200mg/m2 (squamous)')

    pdf.section_title('Sample Size')
    pdf.field_row('Planned Enrollment', '500 subjects (100 per site, 5 sites)')
    pdf.field_row('Current Enrollment', '100 subjects across 5 sites (as of 2025-02-01)')
    pdf.field_row('Power', '80% to detect HR=0.70 in PFS (median PFS 12 vs 8 months)')

    pdf.output(out_path)


# ─────────────────────────────────────────────────────────────────────────────
# Main: generate all PDFs
# ─────────────────────────────────────────────────────────────────────────────
def main():
    base = os.path.dirname(os.path.abspath(__file__))

    # Study-level
    study_dir = os.path.join(base, 'tmf_documents', 'study')
    os.makedirs(study_dir, exist_ok=True)
    gen_protocol_synopsis(os.path.join(study_dir, 'protocol_synopsis_v3.pdf'))
    print(f"  [study] protocol_synopsis_v3.pdf")

    # Per-site documents
    for site_id, s in SITES.items():
        site_dir = os.path.join(base, 'tmf_documents', f'site_{site_id}')
        os.makedirs(site_dir, exist_ok=True)

        gen_delegation_log(site_id, s, os.path.join(site_dir, 'delegation_log_v1.pdf'))
        gen_irb_approval(site_id, s, os.path.join(site_dir, 'irb_approval_2024.pdf'), amendment=False)
        gen_irb_approval(site_id, s, os.path.join(site_dir, 'irb_amendment_v2_1.pdf'), amendment=True)
        gen_icf(site_id, s, os.path.join(site_dir, 'icf_v2_1.pdf'))

        # Also generate superseded v1.0 ICF for sites that have it
        if site_id in ('102', '105'):
            gen_icf(site_id, s, os.path.join(site_dir, 'icf_v1_0.pdf'))

        gen_pi_cv(site_id, s, os.path.join(site_dir, 'pi_cv.pdf'))
        gen_gcp_cert(site_id, s, os.path.join(site_dir, 'gcp_cert_pi.pdf'), person_type='pi')
        gen_gcp_cert(site_id, s, os.path.join(site_dir, 'gcp_cert_coord.pdf'), person_type='coord')
        gen_lab_cert(site_id, s, os.path.join(site_dir, 'lab_certification.pdf'))

        # Drug accountability log (simple)
        pdf = TmfPDF(site_name=s['name'], doc_title='Drug Accountability Log')
        pdf.add_page()
        pdf.section_title('DRUG ACCOUNTABILITY LOG')
        pdf.field_row('Site', f"{site_id} -- {s['name']}")
        pdf.field_row('Drug', 'NovaPlex-450 (Investigational Product)')
        pdf.field_row('Storage', 'Refrigerated 2-8 degrees C, locked pharmacy')
        pdf.ln(4)
        cols = ['Date', 'Subject ID', 'Lot No.', 'Qty Dispensed', 'Qty Returned', 'Balance', 'Pharmacist']
        widths = [22, 25, 22, 25, 25, 22, 29]
        pdf.table_header(cols, widths)
        disp_rows = [
            ['2024-02-15', f'{site_id}-001', 'NVX-2024-001', '2 vials', '0', '18', 'Pharm.'],
            ['2024-03-05', f'{site_id}-002', 'NVX-2024-001', '2 vials', '0', '16', 'Pharm.'],
            ['2024-03-18', f'{site_id}-003', 'NVX-2024-001', '2 vials', '1 partial', '15', 'Pharm.'],
            ['2024-04-01', f'{site_id}-001', 'NVX-2024-002', '2 vials', '0', '13', 'Pharm.'],
            ['2024-04-15', f'{site_id}-004', 'NVX-2024-002', '2 vials', '0', '11', 'Pharm.'],
        ]
        for i, row in enumerate(disp_rows):
            pdf.table_row(row, widths, fill=(i % 2 == 0))
        pdf.ln(4)
        pdf.field_row('Total Dispensed', '10 vials')
        pdf.field_row('Total Returned/Destroyed', '1 partial vial')
        pdf.field_row('Current Balance', '11 vials (reconciled)')
        pdf.output(os.path.join(site_dir, 'drug_accountability.pdf'))

        # Lab normal ranges
        pdf2 = TmfPDF(site_name=s['name'], doc_title='Lab Normal Ranges v2.0')
        pdf2.add_page()
        pdf2.section_title('LABORATORY NORMAL RANGES -- NVX-1218.22')
        pdf2.field_row('Laboratory', s['lab'])
        pdf2.field_row('Version', 'v2.0')
        pdf2.field_row('Effective Date', '2024-06-01')
        pdf2.field_row('Valid Until', '2025-06-01')
        pdf2.ln(4)
        cols2 = ['Test', 'Male Range', 'Female Range', 'Unit', 'Critical Low', 'Critical High']
        widths2 = [40, 28, 30, 22, 25, 25]
        pdf2.table_header(cols2, widths2)
        lab_rows = [
            ['Haemoglobin', '130-175', '120-160', 'g/L', '<80', '>200'],
            ['Platelets', '150-400', '150-400', 'x10^9/L', '<50', '>1000'],
            ['Neutrophils', '1.8-7.5', '1.8-7.5', 'x10^9/L', '<0.5', '>30'],
            ['ALT', '7-56', '7-45', 'U/L', 'N/A', '>500'],
            ['AST', '10-40', '10-40', 'U/L', 'N/A', '>500'],
            ['Creatinine', '62-106', '44-80', 'umol/L', 'N/A', '>500'],
            ['eGFR', '>60', '>60', 'mL/min', '<20', 'N/A'],
            ['Total Bili', '3-17', '3-17', 'umol/L', 'N/A', '>170'],
            ['TSH', '0.4-4.0', '0.4-4.0', 'mU/L', '<0.1', '>10'],
        ]
        for i, row in enumerate(lab_rows):
            pdf2.table_row(row, widths2, fill=(i % 2 == 0))
        pdf2.output(os.path.join(site_dir, 'lab_normal_ranges.pdf'))

        # Follow-up letter (simple)
        last_visit = 'IMV-2' if site_id == '101' else ('IMV-1' if site_id in ('103', '105') else 'IMV-2')
        pdf3 = TmfPDF(site_name=s['name'], doc_title=f'Follow-up Letter -- {last_visit}')
        pdf3.add_page()
        pdf3.section_title(f'MONITORING VISIT FOLLOW-UP LETTER')
        pdf3.field_row('To', f"{s['pi']}, {s['name']}")
        pdf3.field_row('From', 'CRA / Clinical Operations -- NexaVance Therapeutics')
        pdf3.field_row('Re', f"Protocol NVX-1218.22 -- Follow-up to {last_visit}")
        pdf3.field_row('Date', '2025-01-17' if site_id == '101' else '2024-12-06')
        pdf3.ln(4)
        pdf3.body_text(
            f'Dear {s["pi"]},\n\n'
            f'Thank you for your time and co-operation during the recent monitoring visit to {s["name"]}. '
            f'This letter summarises the outstanding action items identified during the visit that require '
            f'your attention and follow-up prior to the next monitoring visit.\n\n'
            f'Please review the action items listed and ensure resolution by the due dates indicated. '
            f'Please confirm completion of each action item in writing to the CRA.'
        )
        pdf3.ln(2)
        pdf3.section_title('Outstanding Action Items')
        pdf3.body_text('Please refer to the attached Monitoring Visit Report for full details of each finding.')
        pdf3.ln(4)
        pdf3.body_text(
            'If you have any questions regarding the action items listed, please do not hesitate to '
            'contact your assigned CRA. We appreciate your ongoing commitment to this important study.'
        )
        pdf3.ln(6)
        pdf3.cell(60, 0.5, '', border='B')
        pdf3.ln(4)
        pdf3.set_font('Helvetica', '', 9)
        pdf3.cell(60, 5, 'CRA Signature')
        pdf3.output(os.path.join(site_dir, 'followup_imv2.pdf' if site_id == '101' else
                                 ('followup_imv1.pdf' if site_id in ('102', '103', '105') else 'followup_imv2.pdf')))

        # SAE narrative for site 101 only
        if site_id == '101':
            pdf4 = TmfPDF(site_name=s['name'], doc_title='SAE Narrative -- Subject 101-901')
            pdf4.add_page()
            pdf4.section_title('SERIOUS ADVERSE EVENT NARRATIVE')
            pdf4.field_row('Subject ID', '101-901')
            pdf4.field_row('Subject Initials', 'M.C.')
            pdf4.field_row('Protocol', 'NVX-1218.22')
            pdf4.field_row('SAE Term', 'Immune-Mediated Myocarditis / Cardiac Arrest')
            pdf4.field_row('CTCAE Grade', '4 (Life-threatening)')
            pdf4.field_row('Causality', 'Related to NovaPlex-450 (probable)')
            pdf4.field_row('Onset Date', '2024-08-14')
            pdf4.field_row('Report Date', '2024-08-15 (15-day initial report submitted)')
            pdf4.field_row('Status', 'Ongoing (subject hospitalised)')
            pdf4.ln(4)
            pdf4.section_title('Narrative')
            pdf4.body_text(
                'Subject 101-901 is a 58-year-old female with advanced NSCLC (Stage IV, non-squamous) '
                'randomised to NovaPlex-450 on 2024-06-01 (Cycle 1 Day 1).\n\n'
                'On 2024-08-14 (Cycle 3 Day 14), subject presented to emergency department with acute '
                'chest pain, dyspnoea, and hypotension. ECG demonstrated ST elevation in multiple leads. '
                'High-sensitivity troponin I was markedly elevated at 8,450 ng/L (ULN: 52 ng/L). '
                'Echocardiography demonstrated global LV dysfunction with LVEF 25% (baseline: 62%).\n\n'
                'Cardiac MRI confirmed immune-mediated myocarditis. Subject suffered witnessed cardiac '
                'arrest (VF) on 2024-08-15, successfully resuscitated with defibrillation. Transferred '
                'to cardiac ICU. NovaPlex-450 permanently discontinued.\n\n'
                'Treatment: IV methylprednisolone 1g/day x 3 days, then oral prednisolone 1mg/kg/day '
                'with planned taper. Cardiology review ongoing. Subject remains hospitalised.'
            )
            pdf4.section_title('Regulatory Reporting')
            pdf4.field_row('15-day report submitted', '2024-08-15 to FDA/EMA')
            pdf4.field_row('Follow-up report due', '2024-09-14')
            pdf4.output(os.path.join(site_dir, 'sae_narrative_901.pdf'))

        print(f"  [site_{site_id}] {len(os.listdir(site_dir))} documents generated in {site_dir}")

    print("\nTMF PDF generation complete.")
    total = sum(len(os.listdir(os.path.join(base, 'tmf_documents', d)))
                for d in os.listdir(os.path.join(base, 'tmf_documents'))
                if os.path.isdir(os.path.join(base, 'tmf_documents', d)))
    print(f"Total PDFs generated: {total}")


if __name__ == '__main__':
    print("Generating synthetic TMF PDF documents...")
    main()
