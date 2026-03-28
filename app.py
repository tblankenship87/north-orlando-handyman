import os
import uuid
import base64
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///handyman.db')
# Ensure directory exists for SQLite file paths
if _db_url.startswith('sqlite:///'):
    _db_path = _db_url.replace('sqlite:////', '/').replace('sqlite:///', '')
    _db_dir = os.path.dirname(_db_path)
    if _db_dir:
        os.makedirs(_db_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'heic', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'handyman2026')

# Suggested line items per service — Kyle adjusts these to his actual rates
SERVICE_QUOTE_TEMPLATES = {
    'French Drain Installation': [
        {'description': 'French drain pipe (perforated)', 'quantity': 50, 'unit_price': 2.50},
        {'description': 'Gravel/aggregate (per ton)', 'quantity': 3, 'unit_price': 55.00},
        {'description': 'Filter fabric / landscape cloth', 'quantity': 1, 'unit_price': 45.00},
        {'description': 'Excavation & labor (hours)', 'quantity': 6, 'unit_price': 75.00},
        {'description': 'Cleanup & haul away', 'quantity': 1, 'unit_price': 75.00},
    ],
    'Sprinkler Service and Repair': [
        {'description': 'Service call / diagnostic', 'quantity': 1, 'unit_price': 75.00},
        {'description': 'Labor (hours)', 'quantity': 2, 'unit_price': 65.00},
        {'description': 'Parts & materials', 'quantity': 1, 'unit_price': 50.00},
    ],
    'Faucet and Shower Repair': [
        {'description': 'Labor (hours)', 'quantity': 1.5, 'unit_price': 65.00},
        {'description': 'Parts & materials', 'quantity': 1, 'unit_price': 40.00},
    ],
    'Lighting and Fan Installation': [
        {'description': 'Labor (hours)', 'quantity': 2, 'unit_price': 65.00},
        {'description': 'Parts & materials', 'quantity': 1, 'unit_price': 30.00},
    ],
    'Wall Repair / Drywall': [
        {'description': 'Drywall patch & repair (sq ft)', 'quantity': 10, 'unit_price': 8.00},
        {'description': 'Labor (hours)', 'quantity': 2, 'unit_price': 65.00},
        {'description': 'Materials (joint compound, tape, etc.)', 'quantity': 1, 'unit_price': 25.00},
    ],
    'Tile Replacement / Installation': [
        {'description': 'Tile installation (sq ft)', 'quantity': 20, 'unit_price': 12.00},
        {'description': 'Tile & materials', 'quantity': 1, 'unit_price': 80.00},
        {'description': 'Labor (hours)', 'quantity': 4, 'unit_price': 65.00},
    ],
    'Furniture Assembly': [
        {'description': 'Assembly labor (hours)', 'quantity': 2, 'unit_price': 55.00},
    ],
    'Dishwasher Installation': [
        {'description': 'Installation labor', 'quantity': 1, 'unit_price': 150.00},
        {'description': 'Parts & fittings', 'quantity': 1, 'unit_price': 25.00},
    ],
    'General Repairs / Other': [
        {'description': 'Labor (hours)', 'quantity': 2, 'unit_price': 65.00},
        {'description': 'Materials', 'quantity': 1, 'unit_price': 30.00},
    ],
}

SERVICE_TYPES = [
    'Sprinkler Service and Repair',
    'French Drain Installation',
    'Door Adjustments',
    'Caulk and Grout',
    'Window Treatments',
    'Wall Repair / Drywall',
    'Shelf and Picture Hanging',
    'Faucet and Shower Repair',
    'Furniture Assembly',
    'Bathroom Fixtures',
    'Lighting and Fan Installation',
    'A/C Condensation Line Cleanout',
    'Room Ventilation',
    'Washing Machine Deep Cleaning',
    'Smoke / CO2 Detector Replacement',
    'Dishwasher Installation',
    'Bathroom Fan Replacement',
    'Doorbell Installation',
    'Cabinet Upgrades',
    'Baby Proofing',
    'Reverse Osmosis Water Installation',
    'Tile Replacement / Installation',
    'Kitchen and Bath Backsplash',
    'Stucco Repair',
    'Custom Fireplace Build',
    'General Repairs / Other',
]

LEAD_SOURCES = ['Google Search', 'Referral', 'Repeat Client', 'Facebook Recommendation', 'Facebook Ad', 'Yelp', 'Nextdoor', 'Physical Sign', 'Other']


# ── Models ──────────────────────────────────────────────────────────────────

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    service_type = db.Column(db.String(100), nullable=False)
    preferred_date = db.Column(db.String(30))
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(50))
    status = db.Column(db.String(30), default='new')  # new/contacted/quoted/booked/complete/lost
    notes = db.Column(db.Text)
    photo_filename = db.Column(db.String(200))  # kept for reference
    photo_data = db.Column(db.Text)             # base64 encoded image stored in DB
    photo_mime = db.Column(db.String(50))       # e.g. image/jpeg
    photos_json = db.Column(db.Text)            # JSON array of {data, mime, filename} for multiple photos
    tier = db.Column(db.String(10))             # '1' = flat-rate booking, '' = custom quote
    urgency = db.Column(db.String(30))          # asap / 2weeks / 2months / flexible
    building_type = db.Column(db.String(50))    # Single Family / Condo / Apartment / Commercial / Other
    materials = db.Column(db.String(50))        # have / will_buy / need_help / not_needed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quotes = db.relationship('Quote', backref='lead', lazy=True)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='customer', lazy=True)
    quotes = db.relationship('Quote', backref='customer', lazy=True)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    title = db.Column(db.String(200), nullable=False)
    service_type = db.Column(db.String(100))
    scheduled_date = db.Column(db.String(30))
    status = db.Column(db.String(30), default='pending')  # pending/scheduled/in_progress/complete
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quotes = db.relationship('Quote', backref='job', lazy=True)


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    token = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), default='draft')  # draft/sent/approved/rejected
    subtotal = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    items = db.relationship('QuoteItem', backref='quote', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='quote', lazy=True)


class QuoteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    line_total = db.Column(db.Float, default=0.0)


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    token = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), default='unpaid')  # unpaid/paid
    amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)


# ── Helpers ─────────────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


STATUS_COLORS = {
    'new': 'primary', 'contacted': 'warning', 'quoted': 'info',
    'booked': 'success', 'complete': 'secondary', 'lost': 'danger',
    'draft': 'secondary', 'sent': 'info', 'approved': 'success', 'rejected': 'danger',
    'pending': 'warning', 'scheduled': 'info', 'in_progress': 'primary',
    'unpaid': 'warning', 'paid': 'success',
}


# ── Public Routes ────────────────────────────────────────────────────────────

FLAT_RATE_SERVICES = [
    {
        "category": "Bathroom",
        "emoji": "🚿",
        "services": [
            {"name": "Bathroom Fan Replacement", "service_type": "Bathroom Fan Replacement", "desc": "Remove old fan, install new (fan provided by homeowner). Includes wiring and drywall patch if needed.", "time": "2–3 hrs", "price": 175, "photo_url": "https://images.unsplash.com/photo-1572081790780-1a7739896259?w=400&h=300&fit=crop"},
            {"name": "Faucet or Shower Repair", "service_type": "Faucet and Shower Repair", "desc": "Fix leaky faucet, replace cartridge, or swap out a faucet. Parts provided by homeowner.", "time": "1–2 hrs", "price": 125, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20250218_030317943-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Caulk & Grout Refresh", "service_type": "Caulk and Grout", "desc": "Remove old caulk and grout, clean, regrout and recaulk tub or shower surround.", "time": "2–3 hrs", "price": 150, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20230616_0200478123.jpg?resize=400%2C300&ssl=1"},
            {"name": "Toilet Repair or Replace", "service_type": "Bathroom Fixtures", "desc": "Fix running toilet, replace flapper, or swap out toilet. Parts/fixture provided by homeowner.", "time": "1–2 hrs", "price": 110, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20250218_033320193-scaled.jpg?resize=400%2C300&ssl=1"},
        ]
    },
    {
        "category": "Kitchen",
        "emoji": "🍳",
        "services": [
            {"name": "Dishwasher Installation", "service_type": "Dishwasher Installation", "desc": "Remove old dishwasher and install new one. Connections must be accessible.", "time": "2–3 hrs", "price": 200, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20250104_164620566-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Kitchen Faucet Replacement", "service_type": "Faucet and Shower Repair", "desc": "Swap out kitchen faucet. New faucet provided by homeowner.", "time": "1–2 hrs", "price": 125, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20250104_163820582-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Cabinet Hardware Upgrade", "service_type": "Cabinet Upgrades", "desc": "Remove old pulls/knobs and install new hardware on up to 20 cabinets.", "time": "1–2 hrs", "price": 95, "photo_url": "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?w=400&h=250&fit=crop"},
            {"name": "Under-Sink Reverse Osmosis Install", "service_type": "Reverse Osmosis Water Installation", "desc": "Install RO water filter system under kitchen sink. System provided by homeowner.", "time": "2–3 hrs", "price": 200, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20250218_031349396-scaled.jpg?resize=400%2C300&ssl=1"},
        ]
    },
    {
        "category": "General & Electrical",
        "emoji": "🔧",
        "services": [
            {"name": "Ceiling Fan Installation", "service_type": "Lighting and Fan Installation", "desc": "Install ceiling fan where existing light fixture is present. Fan provided by homeowner.", "time": "1–2 hrs", "price": 130, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20220728_031438137-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Light Fixture Replacement", "service_type": "Lighting and Fan Installation", "desc": "Swap out up to 3 light fixtures. Fixtures provided by homeowner.", "time": "1–2 hrs", "price": 110, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20220728_031438137-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Doorbell Installation", "service_type": "Doorbell Installation", "desc": "Install wired or smart doorbell. Device provided by homeowner.", "time": "1 hr", "price": 95, "photo_url": ""},
            {"name": "Smoke & CO2 Detector Replacement", "service_type": "Smoke / CO2 Detector Replacement", "desc": "Replace up to 6 detectors. Detectors provided by homeowner.", "time": "1 hr", "price": 85, "photo_url": ""},
        ]
    },
    {
        "category": "Doors, Walls & Assembly",
        "emoji": "🚪",
        "services": [
            {"name": "Door Adjustment or Repair", "service_type": "Door Adjustments", "desc": "Fix sticking, sagging, or misaligned interior door. Includes hinge adjustment and strike plate.", "time": "1 hr", "price": 95, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20250218_115704096-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Furniture Assembly", "service_type": "Furniture Assembly", "desc": "Assemble flat-pack furniture — beds, desks, shelving, dressers. Price per item, up to 2 hrs.", "time": "1–2 hrs", "price": 95, "photo_url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=250&fit=crop"},
            {"name": "Shelf & TV Mount Installation", "service_type": "Shelf and Picture Hanging", "desc": "Mount up to 3 shelves or one TV mount. Hardware included.", "time": "1–2 hrs", "price": 95, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/FirePlace-scaled.jpg?resize=400%2C300&ssl=1"},
            {"name": "Wall Repair / Drywall Patch", "service_type": "Wall Repair / Drywall", "desc": "Patch holes up to 6\" in drywall, texture match, and paint ready.", "time": "1–2 hrs", "price": 120, "photo_url": "https://i0.wp.com/northorlandohandyman.com/wp-content/uploads/2025/02/PXL_20221231_232501103-scaled.jpg?resize=400%2C300&ssl=1"},
        ]
    },
]

@app.route('/')
def index():
    return redirect(url_for('book_landing'))

@app.route('/book')
def book_landing():
    return render_template('book.html', flat_rate_services=FLAT_RATE_SERVICES)

@app.route('/services')
def services_redirect():
    return redirect(url_for('book_landing'))


@app.route('/request', methods=['GET', 'POST'])
def request_form():
    if request.method == 'POST':
        # Handle multiple photo uploads (up to 5)
        photos = []
        photo_data = None
        photo_mime = None
        photo_filename = None
        files = request.files.getlist('photos')
        for file in files[:5]:
            if file and file.filename and allowed_file(file.filename):
                mime = file.content_type or 'image/jpeg'
                data = base64.b64encode(file.read()).decode('utf-8')
                fname = secure_filename(file.filename)
                photos.append({'data': data, 'mime': mime, 'filename': fname})
                if not photo_data:
                    photo_data = data
                    photo_mime = mime
                    photo_filename = fname

        lead = Lead(
            name=request.form['name'],
            phone=request.form['phone'],
            email=request.form['email'],
            address=request.form.get('address', ''),
            service_type=request.form['service_type'],
            preferred_date=request.form.get('preferred_date', ''),
            description=request.form['description'],
            source=request.form.get('source', ''),
            tier=request.form.get('tier', ''),
            urgency=request.form.get('urgency', ''),
            building_type=request.form.get('building_type', ''),
            materials=request.form.get('materials', ''),
            photo_filename=photo_filename,
            photo_data=photo_data,
            photo_mime=photo_mime,
            photos_json=json.dumps(photos) if photos else None,
        )
        db.session.add(lead)
        db.session.commit()

        print(f"\n🔔 NEW LEAD: {lead.name} | {lead.phone} | {lead.service_type}\n")
        fire_n8n_webhook(lead)

        return redirect(url_for('request_thanks'))
    prefill_service = request.args.get('service', '')
    prefill_tier = request.args.get('tier', '')
    return render_template('request.html', services=SERVICE_TYPES, sources=LEAD_SOURCES,
                           prefill_service=prefill_service, prefill_tier=prefill_tier)


@app.route('/request/thanks')
def request_thanks():
    return render_template('request_thanks.html')


@app.route('/quote/<token>', methods=['GET', 'POST'])
def quote_view(token):
    quote = Quote.query.filter_by(token=token).first_or_404()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve' and quote.status == 'sent':
            quote.status = 'approved'
            quote.approved_at = datetime.utcnow()
            if quote.job_id:
                job = Job.query.get(quote.job_id)
                if job:
                    job.status = 'scheduled'
            db.session.commit()
            flash('Quote approved! Kyle will be in touch to confirm the schedule.', 'success')
        elif action == 'reject':
            quote.status = 'rejected'
            db.session.commit()
            flash('Quote declined. Feel free to reach out if you have questions.', 'info')
        return redirect(url_for('quote_view', token=token))
    return render_template('quote_view.html', quote=quote, status_colors=STATUS_COLORS)


@app.route('/invoice/<token>', methods=['GET', 'POST'])
def invoice_view(token):
    invoice = Invoice.query.filter_by(token=token).first_or_404()
    if request.method == 'POST':
        # TODO: Replace with real Stripe payment integration
        invoice.status = 'paid'
        invoice.paid_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('invoice_paid', token=token))
    return render_template('invoice_view.html', invoice=invoice)


@app.route('/invoice/<token>/paid')
def invoice_paid(token):
    invoice = Invoice.query.filter_by(token=token).first_or_404()
    return render_template('invoice_paid.html', invoice=invoice)


# ── Admin Routes ─────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    new_leads = Lead.query.filter_by(status='new').count()
    open_jobs = Job.query.filter(Job.status.in_(['pending', 'scheduled', 'in_progress'])).count()
    pending_quotes = Quote.query.filter_by(status='sent').count()
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(8).all()
    upcoming_jobs = Job.query.filter(Job.status != 'complete').order_by(Job.created_at.desc()).limit(6).all()
    unpaid_invoices = Invoice.query.filter_by(status='unpaid').all()
    revenue = sum(i.amount for i in Invoice.query.filter_by(status='paid').all())
    return render_template('admin/dashboard.html',
        new_leads=new_leads, open_jobs=open_jobs,
        pending_quotes=pending_quotes, revenue=revenue,
        recent_leads=recent_leads, upcoming_jobs=upcoming_jobs,
        status_colors=STATUS_COLORS)


@app.route('/admin/leads')
@admin_required
def admin_leads():
    status = request.args.get('status', '')
    if status:
        leads = Lead.query.filter_by(status=status).order_by(Lead.created_at.desc()).all()
    else:
        leads = Lead.query.order_by(Lead.created_at.desc()).all()
    statuses = ['new', 'contacted', 'quoted', 'booked', 'complete', 'lost']
    return render_template('admin/leads.html', leads=leads, statuses=statuses,
                           current_status=status, status_colors=STATUS_COLORS)


@app.route('/admin/leads/<int:lead_id>', methods=['GET', 'POST'])
@admin_required
def admin_lead_detail(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if request.method == 'POST':
        lead.status = request.form.get('status', lead.status)
        lead.notes = request.form.get('notes', lead.notes)
        db.session.commit()
        flash('Lead updated.', 'success')
        return redirect(url_for('admin_lead_detail', lead_id=lead_id))
    statuses = ['new', 'contacted', 'quoted', 'booked', 'complete', 'lost']
    existing_quote = Quote.query.filter_by(lead_id=lead_id).first()
    lead_photos = json.loads(lead.photos_json) if lead.photos_json else []
    return render_template('admin/lead_detail.html', lead=lead, statuses=statuses,
                           existing_quote=existing_quote, status_colors=STATUS_COLORS,
                           lead_photos=lead_photos)


@app.route('/admin/leads/<int:lead_id>/convert', methods=['POST'])
@admin_required
def admin_lead_convert(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    # Create or find customer
    customer = Customer.query.filter_by(email=lead.email).first()
    if not customer:
        customer = Customer(
            name=lead.name, phone=lead.phone,
            email=lead.email, address=lead.address
        )
        db.session.add(customer)
        db.session.flush()
    # Reuse existing job for this lead if one already exists (prevents duplicates)
    job = Job.query.filter_by(lead_id=lead.id).first()
    if not job:
        job = Job(
            customer_id=customer.id, lead_id=lead.id,
            title=lead.service_type, service_type=lead.service_type,
            scheduled_date=lead.preferred_date
        )
        db.session.add(job)
        db.session.flush()
    lead.status = 'quoted'
    db.session.commit()
    return redirect(url_for('admin_quote_new', job_id=job.id))


@app.route('/admin/quotes/new')
@admin_required
def admin_quote_new():
    job_id = request.args.get('job_id', type=int)
    job = Job.query.get_or_404(job_id) if job_id else None
    template_items = []
    if job and job.service_type:
        template_items = SERVICE_QUOTE_TEMPLATES.get(job.service_type,
            SERVICE_QUOTE_TEMPLATES.get('General Repairs / Other', []))
    return render_template('admin/quote_builder.html', job=job,
                           services=SERVICE_TYPES, template_items=template_items)


@app.route('/admin/quotes', methods=['GET', 'POST'])
@admin_required
def admin_quotes():
    if request.method == 'POST':
        job_id = request.form.get('job_id', type=int)
        job = Job.query.get(job_id) if job_id else None
        customer_id = job.customer_id if job else None

        quote = Quote(
            job_id=job_id, customer_id=customer_id,
            lead_id=job.lead_id if job else None,
            notes=request.form.get('notes', ''),
            tax_rate=float(request.form.get('tax_rate', 0) or 0),
        )
        db.session.add(quote)
        db.session.flush()

        subtotal = 0.0
        descs = request.form.getlist('desc[]')
        qtys = request.form.getlist('qty[]')
        prices = request.form.getlist('price[]')
        for desc, qty, price in zip(descs, qtys, prices):
            if desc.strip():
                qty = float(qty or 1)
                price = float(price or 0)
                total = qty * price
                subtotal += total
                item = QuoteItem(quote_id=quote.id, description=desc,
                                 quantity=qty, unit_price=price, line_total=total)
                db.session.add(item)

        quote.subtotal = subtotal
        quote.total = subtotal + (subtotal * quote.tax_rate / 100)
        db.session.commit()
        flash('Quote saved.', 'success')
        return redirect(url_for('admin_quote_detail', quote_id=quote.id))

    quotes = Quote.query.order_by(Quote.created_at.desc()).all()
    return render_template('admin/quotes.html', quotes=quotes, status_colors=STATUS_COLORS)


@app.route('/admin/quotes/<int:quote_id>')
@admin_required
def admin_quote_detail(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    quote_url = url_for('quote_view', token=quote.token, _external=True)
    return render_template('admin/quote_detail.html', quote=quote,
                           quote_url=quote_url, status_colors=STATUS_COLORS)


@app.route('/admin/quotes/<int:quote_id>/delete', methods=['POST'])
@admin_required
def admin_quote_delete(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    # Reset lead status back to 'contacted' so it goes back in the queue
    if quote.lead_id:
        lead = Lead.query.get(quote.lead_id)
        if lead:
            lead.status = 'contacted'
    for item in quote.items:
        db.session.delete(item)
    db.session.delete(quote)
    db.session.commit()
    flash('Quote discarded. Lead moved back to queue.', 'info')
    return redirect(url_for('admin_leads'))


@app.route('/admin/quotes/<int:quote_id>/edit')
@admin_required
def admin_quote_edit(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    job = Job.query.get(quote.job_id) if quote.job_id else None
    return render_template('admin/quote_builder.html', job=job,
                           services=SERVICE_TYPES, template_items=quote.items,
                           edit_quote=quote)


@app.route('/admin/quotes/<int:quote_id>/update', methods=['POST'])
@admin_required
def admin_quote_update(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    # Clear existing items
    for item in quote.items:
        db.session.delete(item)
    db.session.flush()

    subtotal = 0.0
    descs = request.form.getlist('desc[]')
    qtys = request.form.getlist('qty[]')
    prices = request.form.getlist('price[]')
    for desc, qty, price in zip(descs, qtys, prices):
        if desc.strip():
            qty = float(qty or 1)
            price = float(price or 0)
            total = qty * price
            subtotal += total
            item = QuoteItem(quote_id=quote.id, description=desc,
                             quantity=qty, unit_price=price, line_total=total)
            db.session.add(item)

    quote.subtotal = subtotal
    quote.tax_rate = float(request.form.get('tax_rate', 0) or 0)
    quote.total = subtotal + (subtotal * quote.tax_rate / 100)
    quote.notes = request.form.get('notes', '')
    quote.status = 'draft'  # reset to draft on edit
    db.session.commit()
    flash('Quote updated.', 'success')
    return redirect(url_for('admin_quote_detail', quote_id=quote_id))


@app.route('/admin/quotes/<int:quote_id>/send', methods=['POST'])
@admin_required
def admin_quote_send(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    quote.status = 'sent'
    quote.sent_at = datetime.utcnow()
    db.session.commit()
    quote_url = url_for('quote_view', token=quote.token, _external=True)
    flash(f'Quote marked as sent. Share this link with the customer: {quote_url}', 'success')
    return redirect(url_for('admin_quote_detail', quote_id=quote_id))


@app.route('/admin/invoices', methods=['GET', 'POST'])
@admin_required
def admin_invoices():
    if request.method == 'POST':
        quote_id = request.form.get('quote_id', type=int)
        quote = Quote.query.get_or_404(quote_id)
        invoice = Invoice(quote_id=quote_id, job_id=quote.job_id, amount=quote.total)
        db.session.add(invoice)
        db.session.commit()
        flash('Invoice created.', 'success')
        return redirect(url_for('admin_invoices'))
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('admin/invoices.html', invoices=invoices, status_colors=STATUS_COLORS)


@app.route('/admin/customers')
@admin_required
def admin_customers():
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('admin/customers.html', customers=customers)


@app.route('/admin/customers/<int:customer_id>')
@admin_required
def admin_customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('admin/customer_detail.html', customer=customer,
                           status_colors=STATUS_COLORS)


@app.route('/admin/jobs')
@admin_required
def admin_jobs():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('admin/jobs.html', jobs=jobs, status_colors=STATUS_COLORS)


@app.route('/admin/jobs/<int:job_id>/status', methods=['POST'])
@admin_required
def admin_job_status(job_id):
    job = Job.query.get_or_404(job_id)
    job.status = request.form.get('status', job.status)
    db.session.commit()
    flash('Job status updated.', 'success')
    return redirect(url_for('admin_jobs'))


# ── Startup ──────────────────────────────────────────────────────────────────

def fire_n8n_webhook(lead):
    """Fire n8n webhook in background thread — non-blocking."""
    url = os.getenv('N8N_WEBHOOK_URL', '')
    if not url:
        return
    import threading, requests as req_lib
    def _send():
        try:
            payload = {
                'id': lead.id,
                'name': lead.name,
                'phone': lead.phone,
                'email': lead.email,
                'address': lead.address,
                'service_type': lead.service_type,
                'description': lead.description,
                'preferred_date': lead.preferred_date,
                'source': lead.source,
                'tier': lead.tier or '',
                'urgency': lead.urgency or '',
                'building_type': lead.building_type or '',
                'materials': lead.materials or '',
                'photo_count': len(json.loads(lead.photos_json)) if lead.photos_json else (1 if lead.photo_data else 0),
                'submitted_at': lead.created_at.isoformat(),
                'admin_url': f"{os.getenv('RENDER_EXTERNAL_URL', '')}/admin/leads/{lead.id}",
            }
            req_lib.post(url, json=payload, timeout=10)
            print(f"n8n webhook fired for lead {lead.id}")
        except Exception as e:
            print(f"n8n webhook failed (non-fatal): {e}")
    threading.Thread(target=_send, daemon=True).start()


def run_migrations():
    """Add missing columns to existing tables without losing data."""
    from sqlalchemy import text, inspect
    with db.engine.connect() as conn:
        inspector = inspect(db.engine)
        lead_cols = [c['name'] for c in inspector.get_columns('lead')] if 'lead' in inspector.get_table_names() else []
        migrations = [
            ('lead', 'photo_filename', 'VARCHAR(200)'),
            ('lead', 'photo_data',     'TEXT'),
            ('lead', 'photo_mime',     'VARCHAR(50)'),
            ('lead', 'photos_json',    'TEXT'),
            ('lead', 'tier',           'VARCHAR(10)'),
            ('lead', 'urgency',        'VARCHAR(30)'),
            ('lead', 'building_type',  'VARCHAR(50)'),
            ('lead', 'materials',      'VARCHAR(50)'),
        ]
        for table, col, col_type in migrations:
            if table in inspector.get_table_names() and col not in lead_cols:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                print(f'Migration: added {table}.{col}')
        conn.commit()

def dedup_jobs():
    """Remove duplicate jobs created for the same lead (keep the earliest one)."""
    with app.app_context():
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Find lead_ids with more than one job
            result = conn.execute(text(
                "SELECT lead_id, COUNT(*) as cnt FROM job WHERE lead_id IS NOT NULL GROUP BY lead_id HAVING cnt > 1"
            ))
            rows = result.fetchall()
            for row in rows:
                lead_id = row[0]
                # Keep the lowest id (earliest), delete the rest
                dups = conn.execute(text(
                    "SELECT id FROM job WHERE lead_id = :lid ORDER BY id ASC"
                ), {"lid": lead_id}).fetchall()
                keep_id = dups[0][0]
                for dup in dups[1:]:
                    conn.execute(text("DELETE FROM job WHERE id = :id"), {"id": dup[0]})
                    print(f"Dedup: removed duplicate job {dup[0]} for lead {lead_id}")
            conn.commit()

with app.app_context():
    db.create_all()
    run_migrations()
    dedup_jobs()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
