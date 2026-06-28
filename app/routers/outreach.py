from fastapi import APIRouter, HTTPException, status
from app.schemas.outreach import (
    OutreachGenerateRequest,
    OutreachSendRequest,
    OutreachEmail,
    OutreachResponse,
)
from app.services.outreach_engine import OutreachEngine
from app.services.email_service import EmailService

router = APIRouter(prefix="/outreach", tags=["outreach"])


def _split_subject_body(text: str) -> OutreachEmail:
    # Try to find explicit Subject: line first
    lines = [l.rstrip() for l in text.splitlines()]
    subject = None
    body_lines = []
    found_explicit = False
    for i, line in enumerate(lines):
        lower = line.lower().strip()
        if lower.startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_lines = lines[i + 1 :]
            found_explicit = True
            break
    if not found_explicit:
        # Use first non-empty line as subject if reasonably short
        non_empty = [l for l in lines if l.strip()]
        if non_empty:
            candidate = non_empty[0].strip()
            if len(candidate) <= 120:
                subject = candidate
                # body is everything after first occurrence of candidate
                used = False
                for l in lines:
                    if not used and l.strip() == candidate:
                        used = True
                        continue
                    if used:
                        body_lines.append(l)
        # Fallback defaults
        if not subject:
            subject = "Community outreach request – Lawton, OK"
            body_lines = lines

    body = "\n".join(body_lines).strip()
    if not body:
        # If body ended up empty, use full text excluding possible Subject:
        body = "\n".join([l for l in lines if not l.lower().startswith("subject:")]).strip()
    return OutreachEmail(subject=subject, body=body or text)


@router.post("/generate", response_model=OutreachResponse)
async def generate_outreach(req: OutreachGenerateRequest):
    engine = OutreachEngine()
    content = await engine.generate_email(
        company_name=req.company_name,
        contact_name=req.contact_name,
        project_context=req.project_context,
        materials=[m.model_dump() for m in (req.materials or [])],
        call_to_action=req.call_to_action,
    )
    email = _split_subject_body(content)
    return OutreachResponse(email=email, sent=False)


@router.post("/send", response_model=OutreachResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_outreach(req: OutreachSendRequest):
    engine = OutreachEngine()
    content = await engine.generate_email(
        company_name=req.company_name,
        contact_name=req.contact_name,
        project_context=req.project_context,
        materials=[m.model_dump() for m in (req.materials or [])],
        call_to_action=req.call_to_action,
    )
    email = _split_subject_body(content)

    mailer = EmailService()
    ok = await mailer.send_simple_email(
        to_email=req.to_email,
        subject=email.subject,
        body=email.body,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send outreach email")
    return OutreachResponse(email=email, sent=True, to_email=req.to_email)
