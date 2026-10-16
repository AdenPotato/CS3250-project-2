---
name: uml
description: Write or refresh the PlantUML class diagram (uml/class.wsd) and a story's sequence diagram (uml/sequence-US#.wsd) from the models and routes. Due by the end of Sprint 1, and re-run whenever the model or the flow changes.
---

# /uml

Two diagrams, **+5** together: class **+3**, sequence **+2**. Due by the end of Sprint 1, updated in later sprints if the design changes. Take which one from the request; with none, do both.

## Sources

- **Class diagram**: `src/app/models.py` once it exists - read the code, a diagram drawn from memory drifts. Before the code exists, the acceptance criteria in [README.md](../../../README.md#acceptance-criteria) and decisions from `/new-design`.
- **Sequence diagram**: the story's route in `src/app/routes.py` and its criteria.

## Class diagram

`uml/class.wsd` needs at least **User, Vendor or a role, Listing, Reservation and DietaryTag**, their key attributes, and their associations **with multiplicities**. The database tables must be traceable to it. The template ships a stub `User` - replace it.

Pick one way to model the role and say it in a note: a `role` attribute on `User` (simplest), or `Student` and `Vendor` subclasses of `User`. Either satisfies "Vendor or role".

```plantuml
@startuml class
hide circle
skinparam classAttributeIconSize 0

enum Role {
  STUDENT
  VENDOR
}

class User {
  +id : Integer <<PK>>
  +name : String
  +email : String <<unique>>
  +password_hash : String
  +role : Role
  +created_at : DateTime
}

class Listing {
  +id : Integer <<PK>>
  +vendor_id : Integer <<FK>>
  +title : String
  +description : Text
  +portions_total : Integer {1..100}
  +portions_remaining : Integer {>= 0}
  +location : String
  +window_start : DateTime
  +window_end : DateTime
  +cancelled : Boolean
}

class Reservation {
  +id : Integer <<PK>>
  +student_id : Integer <<FK>>
  +listing_id : Integer <<FK>>
  +portions : Integer {1..2}
  +pickup_code : String(6) <<unique>>
  +status : ReservationStatus
  +created_at : DateTime
}

enum ReservationStatus {
  ACTIVE
  PICKED_UP
  CANCELLED
  NO_SHOW
}

class DietaryTag {
  +id : Integer <<PK>>
  +name : String <<unique>>
}

User "1" -- "0..*" Listing : posts >
User "1" -- "0..*" Reservation : makes >
Listing "1" -- "0..*" Reservation : holds >
Listing "0..*" -- "0..*" DietaryTag : tagged with >
User ..> Role
Reservation ..> ReservationStatus

note "Only a VENDOR posts listings;\nonly a STUDENT makes reservations." as N1
@enduml
```

This is a starting shape, not the answer - match it to the actual models. Add `Rating` (US10) only if that story is built.

## Sequence diagram

`uml/sequence-US<n>.wsd` (rename the template - the `#` is a placeholder) shows **one story's full flow from the browser through the Flask route, any service or model classes, and PostgreSQL**, with **at least one alternative path**. US4 or US7 are the suggested choices.

```plantuml
@startuml sequence-US4
actor Student
participant Browser
participant "Flask route\nreserve()" as Route
participant "ReserveForm" as Form
participant "Reservation\nmodel" as Model
database PostgreSQL as DB

Student -> Browser : choose portions, click Reserve
Browser -> Route : POST /listings/<id>/reserve
Route -> Form : validate_on_submit()
Route -> DB : SELECT active reservation\nfor student + listing
alt already has an active reservation
  Route --> Browser : 200, "You already have a reservation"
else no reservation yet
  Route -> DB : UPDATE listing SET remaining = remaining - n\nWHERE id = :id AND remaining >= n
  alt 0 rows updated (not enough portions)
    Route --> Browser : 200, "Not enough portions left"
  else 1 row updated
    Route -> Model : new Reservation(pickup_code)
    Model -> DB : INSERT reservation
    Route -> DB : COMMIT
    Route --> Browser : 302 -> reservation page
    Browser --> Student : pickup code ABC123
  end
end
@enduml
```

Every message is something the code actually does, in the order it does it. The conditional `UPDATE` is what makes US4.4 visible in the diagram.

## Render and commit

```
plantuml uml/class.wsd uml/sequence-US4.wsd
```

Or the PlantUML extension in VS Code. Commit the rendered PNGs beside the sources so the grader does not have to render them.

## Keep them true

A diagram that disagrees with the code is worth less than one that is plainly incomplete. Re-run after any `/new-model`, and when the story's route changes.
