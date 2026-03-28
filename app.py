import os
import uuid
import base64
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

LEAD_SOURCES = ['Google', 'Referral', 'Facebook', 'Nextdoor', 'Door Hanger', 'Other']


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

@app.route('/')
def index():
    return redirect(url_for('request_form'))


@app.route('/request', methods=['GET', 'POST'])
def request_form():
    if request.method == 'POST':
        photo_data = None
        photo_mime = None
        photo_filename = None
        file = request.files.get('photo')
        if file and file.filename and allowed_file(file.filename):
            mime = file.content_type or 'image/jpeg'
            photo_data = base64.b64encode(file.read()).decode('utf-8')
            photo_mime = mime
            photo_filename = secure_filename(file.filename)

        lead = Lead(
            name=request.form['name'],
            phone=request.form['phone'],
            email=request.form['email'],
            address=request.form.get('address', ''),
            service_type=request.form['service_type'],
            preferred_date=request.form.get('preferred_date', ''),
            description=request.form['description'],
            source=request.form.get('source', ''),
            photo_filename=photo_filename,
            photo_data=photo_data,
            photo_mime=photo_mime,
        )
        db.session.add(lead)
        db.session.commit()

        # TODO: Replace with real email/SMS notification
        print(f"\n🔔 NEW LEAD: {lead.name} | {lead.phone} | {lead.service_type}\n")

        return redirect(url_for('request_thanks'))
    return render_template('request.html', services=SERVICE_TYPES, sources=LEAD_SOURCES)


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
    return render_template('admin/lead_detail.html', lead=lead, statuses=statuses,
                           existing_quote=existing_quote, status_colors=STATUS_COLORS)


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
    # Create job
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

def run_migrations():
    """Add missing columns to existing tables without losing data."""
    from sqlalchemy import text, inspect
    with db.engine.connect() as conn:
        inspector = inspect(db.engine)
        # Migrate lead table
        lead_cols = [c['name'] for c in inspector.get_columns('lead')] if 'lead' in inspector.get_table_names() else []
        migrations = [
            ('lead', 'photo_filename', 'VARCHAR(200)'),
            ('lead', 'photo_data',     'TEXT'),
            ('lead', 'photo_mime',     'VARCHAR(50)'),
        ]
        for table, col, col_type in migrations:
            if table in inspector.get_table_names() and col not in lead_cols:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                print(f'Migration: added {table}.{col}')
        conn.commit()

with app.app_context():
    db.create_all()
    run_migrations()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
