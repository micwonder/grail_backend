from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.user import UserInDB
from app.crud.user import get_user_by_email
from app.config import settings
import stripe

stripe.api_key = settings.STRIPE_API_KEY

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session(user_mail: str, plan_id: str):
    user = await get_user_by_email(user_mail)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user.email,
            line_items=[{
                'price': plan_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://www.thegrail.app/success',
            cancel_url='https://www.thegrail.app/cancel',
        )
        return session
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/retrieve-subscription")
async def retrieve_subscription(subscription_id: str):
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(subscription_id: str):
    try:
        subscription = stripe.Subscription.delete(subscription_id)
        return subscription
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "charge.succeeded":
        charge = event["data"]["object"]
        # Handle successful charge
        print(f"Charge succeeded: {charge}")
    elif event["type"] == "charge.failed":
        charge = event["data"]["object"]
        # Handle failed charge
        print(f"Charge failed: {charge}")
    # Add more event types as needed

    return {"status": "success"}