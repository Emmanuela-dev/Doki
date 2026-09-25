# DoKi 🌱

### AI-Powered B2B Organic Waste Marketplace

DoKi is a digital marketplace that connects businesses that **produce organic waste** with businesses that **need organic waste as a resource**.

Instead of allowing useful organic waste to end up in landfills, DoKi helps businesses discover, trade, and reuse it.

---

## 🌍 The Problem

Kenya generates thousands of tonnes of waste every day, and a large percentage of it is organic waste.

Much of this waste ends up in landfills even though it can be used to produce:

* Compost
* Organic fertilizer
* Biogas
* Black Soldier Fly (BSF) products
* Other circular-economy products

The problem is not only the availability of waste.

The bigger problem is **connection**.

A business may have tonnes of organic waste but not know who needs it, while another business may need the same material but struggle to find a reliable supplier.

Existing solutions are often based on direct relationships, vertically integrated operations, or informal brokers.

**DoKi aims to provide an open digital marketplace where these businesses can find and transact with each other.**

---

## 💡 The Solution

DoKi creates a digital marketplace for organic waste.

### Sellers

Businesses such as:

* Food processors
* Breweries
* Maize and coffee mills
* Dairy and sugar factories
* Hotels

can list their organic waste on the platform.

### Buyers

Businesses such as:

* Compost producers
* Biogas plants
* BSF farms
* Organic fertilizer manufacturers

can search for and purchase the waste they need.

---

## 🔄 How DoKi Works

The basic process is:

```text
Seller has organic waste
        ↓
Upload a photo
        ↓
AI identifies the waste type
        ↓
DoKi creates a structured listing
        ↓
Buyer searches and discovers the listing
        ↓
Buyer and seller agree on the transaction
        ↓
Digital transaction agreement
        ↓
Waste is delivered
        ↓
Buyer confirms delivery
        ↓
Transaction is completed
```

In simple terms:

> **Point. Snap. List. Connect. Trade. Reuse.**

---

## 🤖 AI-Powered Listings

DoKi uses AI to make creating waste listings easier.

A seller can take a photo of their organic waste and upload it to the platform.

The AI helps:

1. Identify the type of waste.
2. Classify the waste.
3. Generate a structured listing.
4. Make the listing easier for buyers to discover.

The seller can then review and confirm the information before publishing.

AI is therefore used to simplify the listing process rather than requiring users to understand complicated waste classifications.

---

## 🤝 Trust & Accountability

DoKi is designed to make transactions more reliable.

### Quality Checklists

Listings can include information about waste quality, purity, and segregation so buyers know what they are purchasing.

### Digital Transaction Agreements

Before a deal proceeds, the buyer and seller agree on important details such as:

* Waste type
* Quantity
* Price
* Delivery date
* Quality requirements

### Payment Protection

The planned platform includes an M-Pesa-based escrow workflow where payment can be held until delivery is confirmed.

### Dispute Handling

Buyers can report problems with a delivered order within a defined dispute period.

Repeated violations can result in sellers being restricted or suspended from the marketplace.

---

## 🏪 Main Users

### 1. Sellers

Businesses that generate organic waste.

They can:

* Create waste listings
* Upload photos
* Use AI classification
* Set quantities and prices
* Manage interested buyers
* Manage transactions

### 2. Buyers

Businesses that need organic waste.

They can:

* Search for waste
* Filter listings
* View seller information
* View waste details
* Express interest
* Agree to transactions
* Confirm deliveries
* Raise disputes

### 3. Administrators

Platform administrators can:

* Manage users
* Review listings
* Verify businesses
* Monitor transactions
* Handle disputes
* Manage waste categories
* Monitor platform activity

---

## 💰 Business Model

DoKi plans to generate revenue primarily when waste is successfully traded.

### Transaction Fees

DoKi can charge a commission on completed transactions.

### Premium Listings

Sellers can pay for increased visibility and featured placement.

### Future Subscriptions

Power users may eventually pay for additional services such as:

* Market analytics
* Demand forecasts
* Supplier insights

---

## 🌱 Environmental Impact

DoKi aims to turn organic waste into a useful resource instead of allowing it to become landfill waste.

Key impact metrics include:

* Tonnes of organic waste diverted from landfills
* Number of successful transactions
* Number of participating businesses
* Waste converted into useful circular products
* Estimated methane emissions avoided

The goal is simple:

> **Less organic waste in landfills and more organic waste returned to the circular economy.**

---

## 🛠️ Planned Technology Stack

The initial platform is planned as a web application.

### Frontend

* Next.js
* TypeScript
* Tailwind CSS

### Backend

* Python
* FastAPI

### Database

* PostgreSQL

### AI

* Computer vision / vision-enabled AI for waste classification

### Storage

* Cloud storage such as AWS S3

### Payments

* M-Pesa / Safaricom Daraja API

### Maps & Location

* Mapbox or Google Maps

### Future Mobile Application

* Flutter

---

## 🏗️ High-Level Architecture

```text
                    DoKi Web Application
                         Next.js
                            │
                            ▼
                       FastAPI API
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        PostgreSQL       AI Service      Storage
             │              │              │
             │              │              │
             └──────────────┼──────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          M-Pesa          Maps        Notifications
```

A Flutter mobile application can be added later and use the same backend API.

---

## 🚀 Project Goals

The initial goal of DoKi is to build a working marketplace that allows:

* Businesses to list organic waste.
* AI to assist with waste classification.
* Buyers to discover available organic waste.
* Buyers and sellers to create transactions.
* Transactions to be managed digitally.
* Waste to be redirected toward useful circular-economy applications.

---

## 🧩 Future Features

Possible future improvements include:

* Mobile application
* Advanced AI waste classification
* Supplier recommendations
* Demand forecasting
* Logistics integration
* Real-time chat
* Business verification
* Seller ratings and reputation
* Advanced marketplace analytics
* Automated notifications
* Geographic and distance-based matching

---

## 🌍 Vision

DoKi aims to make organic waste **discoverable, tradable, and reusable**.

The long-term vision is to create a digital infrastructure that makes it easier for businesses to participate in the circular economy.

> **DoKi — Turning Organic Waste Into Value.**

---

## 📌 Project Status

DoKi is currently being developed as an AI-powered B2B organic waste marketplace.

The first development focus is the **core marketplace and transaction workflow**, followed by AI, trust, payments, and other advanced features.

---

## 👥 Team
Celion Ligalamu
Vane Meta
Emmanuela Omondi

**Focus:** AI + Circular Economy + B2B Marketplace
