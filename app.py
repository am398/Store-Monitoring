from flask import Flask, jsonify, send_file,request
import os
from models import db, init_app
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from services.report_service import ReportService
import uuid
from models.report import Report
import threading

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')
init_app(app)


@app.route('/')
def home():
    print(os.getenv('anuj'))
    return "Hello World"

@app.route('/trigger_report', methods=['POST'])
def trigger_report():
    report_id = str(uuid.uuid4())
    report = Report(id=report_id, status='Running')
    db.session.add(report)
    db.session.commit()

    report_service = ReportService(app)
    # Start the report generation in a separate thread
    threading.Thread(target=report_service.generate_report, args=(report_id,)).start()

    return jsonify({'report_id': report_id})

@app.route('/get_report/<report_id>', methods=['GET'])
def get_report(report_id):
    report = Report.query.get(report_id)
    if report.status == 'Running':
        return jsonify({'status': 'Running'})
    elif report.status == 'Complete':
        return send_file(report.file_path, as_attachment=True)
    else:
        return jsonify({'error': 'Invalid report status'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)