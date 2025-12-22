---


---
# Deep Research with Email Input and Guardrail against Invalid/ Undeliverable Email

### It has following features:

* The report will be output to the markdown area at the bottom of the gradio screen in default. The requester will receive a copy in an email if he/ she choose to leave an email. Therefore, there can be multiple inputs.
* The send_email call in research_manager need to pass multiple inputs to the email_agent. I struggled with it for a while.  Consult with other similar projects in community contributions and settled with the input as a prompt approach.  Thanks to Ed of reminding me that LLM is behind the scene.  LLMs parse all inputs as tokens regardless.
* Email checker is part of workflow if the email is provided and is implemented as an input guardrail. Originally I implemented myself email checker which will do regex, role-based and disposable check first then the MX record resolved by DNS will be checked again a SMTP server.  It works most of time locally.  However, it always receive timeout in HuggingFace. My guessing is that the deployment environment does not have a Firewall (open port) rule to allow SMTP inbound response back. I ends up using https://kickbox.com/.  It does require at least $5 for API integration though it markets the first 100 email is free.
* Email checker will return the final result as the followings and the guradrail will check against the status. The codes in details are in email_checker.py.

```
{"status":"deliverable","reason":"accepted_email"}
```

* verify_mail will catch `InputGuardrailTripwireTriggered` exception and output the the guardrail's output_info
* The workflow will stop if email is requested and email guardrail fails.

### GITHUB code:

https://github.com/threecuptea/agents

### The demo:

https://huggingface.co/spaces/threecuptea/deep_research2
