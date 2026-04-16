## Setup

```bash
# install dependencies
pip install -r requirements.txt

# run
python app.py
```
After this, just open http://127.0.0.1:5000 in your browser. 

## Youtube Presentation

https://www.youtube.com/watch?v=sd_cQRbV6rE

## Design Patterns Used

| Pattern | File | Used for |
|---|---|---|
| Singleton | `patterns/singleton.py` | SessionManager, one shared instance across the app |
| Observer | `patterns/observer.py` | WatchlistManager, notifies renters when a watched car drops in price |
| Mediator | `patterns/mediator.py` | NotificationMediator, handles booking, payment, and message events |
| Builder | `patterns/builder.py` | CarListingBuilder, constructs car listings with required + optional fields |
| Proxy | `patterns/proxy.py` | PaymentProxy, validates before delegating to RealPaymentService |
| Chain of Responsibility | `patterns/chain.py` | PasswordRecoveryChain, three security question handlers |