import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_mail(newsletter_content, from_email, to_email):

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='This week in the world of AI....',
        html_content=newsletter_content,
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        # print(response.body)
        # print(response.headers)
    except Exception as e:
        print(e)

def prepare_newsletter_html(newsletter_content):
    print("Preparing the newsletter...")
    sections_html = ""

    for item in newsletter_content.sections:
        sections_html += f"""
        <div class="section">
            <h2>{item.headline}</h2>
            <p>{item.body}</p>
            <div class="links">
                <a href="{item.source_link}">Read more</a>
            </div>
        </div>
        """

    full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Insights Newsletter</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #f5f7fb;
                    font-family: Arial, sans-serif;
                    color: #374151;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 20px;
                }}
                .header h1 {{
                    color: #111827;
                    font-size: 24px;
                    margin: 0;
                }}
                .header p {{
                    color: #1e3a8a;
                    font-size: 16px;
                    margin: 5px 0 0;
                }}
                .section {{
                    margin: 20px 0;
                    padding: 15px;
                    border-radius: 10px;
                    background-color: #e5e7eb;
                }}
                .section h2 {{
                    color: #1e3a8a;
                    font-size: 20px;
                    margin: 0 0 10px;
                }}
                .section p {{
                    color: #374151;
                    font-size: 14px;
                    margin: 0 0 10px;
                }}
                .links {{
                    margin-top: 10px;
                }}
                .links a {{
                    color: #2563eb;
                    font-weight: bold;
                    text-decoration: none;
                }}
                .links a:hover {{
                    color: #1d4ed8;
                }}
                .footer {{
                    text-align: center;
                    color: #6b7280;
                    font-size: 12px;
                    margin-top: 20px;
                    padding: 10px;
                    border-top: 1px solid #e5e7eb;
                }}
                .cta {{
                    text-align: center;
                    margin-top: 15px;
                }}
                .cta button {{
                    background-color: #2563eb;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 20px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: bold;
                }}
                .cta button:hover {{
                    background-color: #1d4ed8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AI Insights Newsletter</h1>
                    <p>Your source for the latest in AI Innovation and Technology.</p>
                </div>
                {sections_html}
                <div class="footer">
                    © 2026 Ayan Mukherjee. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """  
    print("Newsletter Preparation Finished.")
    return full_html
    