# Resource Hub Recommendation System

## Overview

This project helps users find useful community resources such as food assistance, healthcare clinics, housing support, and job training programs.

The system takes user input (location, income, urgency, and eligibility factors) and recommends the most relevant resources using a scoring-based recommendation system.

This project demonstrates how data-driven decision-making can be applied to solve real-world social problems.

---

## Key Features

* Combines multiple datasets (food, healthcare, housing, job training)
* Cleans and organizes data into a structured format
* Stores data in a SQLite database
* Filters resources based on eligibility (income, student status, household size)
* Ranks results based on location, urgency, and other factors
* Uses county-level data (poverty, unemployment, SNAP usage)
* Displays recommendations using a Streamlit-based graphical user interface
* Provides explanations for why each recommendation was selected

---

## System Architecture

The system consists of four main components:

### 1. Data Pipeline (`fresh_data.py`)

* Loads raw datasets
* Cleans and merges data
* Stores processed data in SQLite database (`resource_hub_fresh.db`)

### 2. Data Loader (`data_loader.py`)

* Loads data from the database
* Prepares it for processing

### 3. Core Logic

* **Eligibility Engine** → checks user eligibility
* **Ranking Engine** → calculates scores based on multiple factors
* **Recommendation Engine** → generates final ranked results

### 4. User Interface (`app.py`)

* Built using Streamlit
* Collects user input
* Displays recommendations and scores

---

## Object-Oriented Design

The system uses multiple classes to organize data and functionality:

* **UserProfile** → stores user input details
* **Resource** → represents each resource
* **EligibilityEngine** → handles eligibility filtering
* **RankingEngine** → calculates match scores

This modular design improves readability, scalability, and maintainability.

---

## Project Structure

RESOURCE_HUB/
│
├── core/
├── data/
├── app.py
├── fresh_data.py
├── requirements.txt
├── test_project.py
└── README.md

---

## How to Run

### Install dependencies

pip install -r requirements.txt

### Run the application

streamlit run app.py

---

## User Inputs

* Resource type (food, healthcare, etc.)
* ZIP code / city / state
* Monthly income
* Household size
* Student status
* Urgency level

---

## Recommendation Logic

Each resource is scored using:

* Location matching
* Eligibility conditions
* Data completeness
* Urgency level
* County-level statistics

The system ranks resources based on a combined score and displays the top results.

---

## Data Handling

The system performs meaningful data I/O by:

* Reading from CSV datasets
* Storing and querying data from a SQLite database
* Processing and filtering data using Python code

---

## Testing

The project includes unit tests using pytest.

To run tests:
pytest

These tests validate core components such as user profile handling and input validation.

---

## Technologies Used

* Python 3.12
* Pandas
* SQLite
* Streamlit
* Pytest

---

## Version Control

This project uses GitHub as a repository for collaboration.

* Each team member contributed multiple substantial commits
* GitHub was used to manage development and track progress

---

## Conclusion

This project demonstrates how data processing, ranking algorithms, and user interface design can be combined to build a practical recommendation system.

It also highlights how technology can be used to support communities by improving access to essential services.
