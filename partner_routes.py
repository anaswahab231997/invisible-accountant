import hashlib
import re
import secrets
from xml.sax.saxutils import escape as xml_escape
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import db
from security import (
    create_practice_token,
    hash_practice_password,
    verify_practice_password,
    verify_practice_session,
)
from rate_limiter import limiter

partner_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@partner_router.get("/partner/register", response_class=HTMLResponse)
async def partner_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="partner_register.html", context={"error": None})


@partner_router.post("/partner/register")
@limiter.limit("3/minute")
async def partner_register_submit(
    request: Request,
    response: Response,
    name: str = Form(...),
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: str = Form(""),
    regulatory_body: str = Form("ICAEW"),
    regulatory_number: str = Form(""),
    company_number: str = Form(""),
    slug: str = Form(...),
    password: str = Form(...),
):
    clean_name = name.strip()
    clean_email = contact_email.strip().lower()
    clean_slug = re.sub(r"[^a-z0-9\-]", "", slug.strip().lower())

    if len(clean_name) < 3:
        return templates.TemplateResponse(
            request=request,
            name="partner_register.html",
            context={"error": "Practice name must be at least 3 characters long."},
            status_code=400,
        )

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
        return templates.TemplateResponse(
            request=request,
            name="partner_register.html",
            context={"error": "Please enter a valid business email address."},
            status_code=400,
        )

    if not clean_slug:
        clean_slug = re.sub(r"[^a-z0-9\-]", "", clean_name.lower().replace(" ", "-"))

    if len(clean_slug) < 3:
        return templates.TemplateResponse(
            request=request,
            name="partner_register.html",
            context={"error": "Practice URL slug must be at least 3 characters long."},
            status_code=400,
        )

    # Check if slug or email exists
    existing_slug = await db.get_practice_by_slug(clean_slug)
    if existing_slug:
        return templates.TemplateResponse(
            request=request,
            name="partner_register.html",
            context={"error": f"The practice slug '{clean_slug}' is already taken. Please choose another."},
        )

    existing_email = await db.get_practice_by_email(clean_email)
    if existing_email:
        return templates.TemplateResponse(
            request=request,
            name="partner_register.html",
            context={"error": "An accountancy practice with this email already exists."},
        )

    # Generate unique firm_code e.g. IA-9284
    firm_code = f"IA-{secrets.randbelow(9000) + 1000}"
    while await db.get_practice_by_code(firm_code):
        firm_code = f"IA-{secrets.randbelow(9000) + 1000}"

    password_hash = hash_practice_password(password)

    practice_id = await db.create_practice(
        name=clean_name,
        slug=clean_slug,
        firm_code=firm_code,
        contact_name=contact_name.strip(),
        contact_email=clean_email,
        contact_phone=contact_phone.strip(),
        company_number=company_number.strip(),
        regulatory_body=regulatory_body.strip(),
        regulatory_number=regulatory_number.strip(),
        password_hash=password_hash,
    )

    token = create_practice_token(practice_id, clean_slug)
    redirect = RedirectResponse("/partner/dashboard", status_code=303)
    redirect.set_cookie(
        key="practice_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=14 * 86400,
    )
    redirect.set_cookie(
        key="partner_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=14 * 86400,
    )
    return redirect


@partner_router.get("/partner/login", response_class=HTMLResponse)
async def partner_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="partner_login.html", context={"error": None})


@partner_router.post("/partner/login")
@limiter.limit("5/minute")
async def partner_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    clean_email = email.strip().lower()
    practice = await db.get_practice_by_email(clean_email)

    if not practice or not verify_practice_password(password, practice.get("password_hash")):
        return templates.TemplateResponse(
            request=request,
            name="partner_login.html",
            context={"error": "Invalid practice email or password. Please verify your credentials."},
            status_code=401,
        )

    token = create_practice_token(practice["id"], practice["slug"])
    redirect = RedirectResponse("/partner/dashboard", status_code=303)
    redirect.set_cookie(
        key="practice_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=14 * 86400,
    )
    redirect.set_cookie(
        key="partner_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=14 * 86400,
    )
    return redirect


@partner_router.get("/partner/logout")
async def partner_logout():
    redirect = RedirectResponse("/partner/login", status_code=303)
    redirect.delete_cookie(key="practice_session", httponly=True, secure=True, samesite="lax")
    redirect.delete_cookie(key="partner_session", httponly=True, secure=True, samesite="lax")
    return redirect


@partner_router.get("/partner/dashboard", response_class=HTMLResponse)
async def partner_dashboard(request: Request, session: dict = Depends(verify_practice_session)):
    practice_id = session["practice_id"]
    practice = await db.get_practice_by_id(practice_id)
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")

    stats = await db.get_practice_stats(practice_id)
    clients = await db.get_practice_clients(practice_id)
    lois = await db.get_practice_lois(practice_id)

    response = templates.TemplateResponse(
        request=request,
        name="partner_dashboard.html",
        context={
            "practice": practice,
            "stats": stats,
            "clients": clients,
            "lois": lois,
        },
    )

    if getattr(request.state, "should_set_practice_cookie", False):
        token = getattr(request.state, "practice_token", None)
        if token:
            response.set_cookie(
                key="practice_session",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=14 * 86400,
            )
            response.set_cookie(
                key="partner_session",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=14 * 86400,
            )

    return response


@partner_router.get("/join/{firm_slug}", response_class=HTMLResponse)
async def client_join_splash(request: Request, firm_slug: str):
    practice = await db.get_practice_by_slug(firm_slug)
    if not practice:
        raise HTTPException(status_code=404, detail="Partner practice not found")

    return templates.TemplateResponse(request=request, name="client_join.html", context={"practice": practice})


@partner_router.post("/partner/loi/sign")
async def partner_loi_sign(
    request: Request,
    signatory_name: str = Form(...),
    signatory_title: str = Form(...),
    firm_legal_name: str = Form(...),
    pledged_seats: int = Form(50),
    firm_address: str = Form(""),
    session: dict = Depends(verify_practice_session),
):
    if not (1 <= pledged_seats <= 100000):
        raise HTTPException(status_code=400, detail="Pledged seats must be between 1 and 100,000")

    practice_id = session["practice_id"]
    practice = await db.get_practice_by_id(practice_id)
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")

    client_ip = request.client.host if request.client else "127.0.0.1"

    # Compute deterministic SHA256 seal
    raw_agreement = f"{practice_id}:{firm_legal_name}:{signatory_name}:{pledged_seats}:{client_ip}"
    doc_hash = hashlib.sha256(raw_agreement.encode("utf-8")).hexdigest()

    safe_sig = xml_escape(signatory_name.strip())

    await db.record_practice_loi(
        practice_id=practice_id,
        signatory_name=signatory_name.strip(),
        signatory_title=signatory_title.strip(),
        firm_legal_name=firm_legal_name.strip(),
        firm_crn=practice.get("company_number", ""),
        firm_address=firm_address.strip(),
        pledged_client_seats=pledged_seats,
        signature_data_url=f"data:image/svg+xml;utf8,<svg><text>{safe_sig}</text></svg>",
        signature_ip_address=client_ip,
        document_sha256=doc_hash,
    )

    return RedirectResponse("/partner/dashboard", status_code=303)
