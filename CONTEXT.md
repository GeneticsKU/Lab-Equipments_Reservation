# Genetics Lab Equipment Reservation

This context defines the language for controlling access to shared laboratory equipment reservations within the Genetics Department at Kasetsart University.

## Language

**KU Identity**:
An institutional identity backed by an email address ending in `@ku.th`.
_Avoid_: public account, external account

**KU Email Verification**:
Proof that a user can receive email at an address ending in `@ku.th`.
_Avoid_: institutional single sign-on, staff-managed identity

**Fallback Identity**:
The launch identity method used when KU does not provide institutional single sign-on.
_Avoid_: institutional SSO, manual account list

**One-Time Code Login**:
A passwordless sign-in method where the user proves mailbox access by entering a short code sent to a verified email address.
_Avoid_: reusable password, institutional SSO

**Applicant**:
A person requesting access to reserve laboratory equipment.
_Avoid_: guest, anonymous user

**Access Approval**:
A departmental decision that allows an Applicant to reserve laboratory equipment.
_Avoid_: open signup, self-activation

**Access Request**:
An Applicant's request to become an Approved User under a named Sponsor.
_Avoid_: registration form, public signup

**Access Request Fields**:
The required information collected when an Applicant submits an Access Request.
_Avoid_: full profile, free-form onboarding dump

**Sponsor View**:
The limited set of request information visible to a Sponsor inside the app.
_Avoid_: global user directory, global reservation visibility

**Operations View**:
The operational data visible to an Operations Manager inside the app.
_Avoid_: hidden reservation state, automatic sponsor authority

**Admin Override**:
The full visibility and recovery authority held by the Admin role across all domains in the app.
_Avoid_: narrow operations role, sponsor-only action

**Delegated Reservation**:
A reservation created by an Operations Manager or Admin on behalf of another user.
_Avoid_: hidden manual booking, unaudited staff action

**Delegated Cancellation**:
A cancellation performed by an Operations Manager or Admin on behalf of another user.
_Avoid_: hidden manual cancellation, unaudited staff action

**Access Request Status**:
The current lifecycle state of an Access Request.
_Avoid_: account status, booking status

**Pending**:
An Access Request Status for a request waiting on sponsor action.
_Avoid_: draft, scheduled

**Approved**:
An Access Request Status for a request accepted by the Sponsor.
_Avoid_: verified email only

**Denied**:
An Access Request Status for a request rejected by the Sponsor.
_Avoid_: expired request

**Expired**:
An Access Request Status for a request that was not acted on in time.
_Avoid_: denied request

**Sponsor Approval**:
The Sponsor's final decision, made from the Sponsor's own authenticated account, that grants an Applicant access to reserve laboratory equipment.
_Avoid_: recommendation, staff activation

**Approved User**:
An Applicant who has received Access Approval and may reserve laboratory equipment.
_Avoid_: open user, public user

**Access Term**:
The period during which an Approved User keeps Booking Access before renewal is required.
_Avoid_: permanent access, indefinite access

**Deactivation**:
The manual removal of a user's Booking Access by an authorized role.
_Avoid_: expiry, cancellation

**Access Restriction**:
A manual reduction of a user's effective booking privileges without fully removing Booking Access.
_Avoid_: deactivation, sponsor denial

**User Category**:
The institutional category used to determine a default Access Term and future booking rules.
_Avoid_: account type, generic role

**Sponsor Capability**:
The permission that allows a person in the Sponsor Directory to grant Sponsor Approval.
_Avoid_: generic admin right, user category

**Booking Access**:
The right for an Approved User to reserve enabled equipment in the system.
_Avoid_: training clearance, room entry

**Booking Quota**:
The limit on how much future reservation capacity an Approved User may hold.
_Avoid_: unlimited booking, collision rule

**Booking Horizon**:
The maximum future time range within which an Approved User may make a reservation.
_Avoid_: access term, permanent access

**Reservation Policy**:
The set of booking rules that governs Booking Horizon, Booking Quota, and maximum reservation duration.
_Avoid_: ad hoc note, equipment detail text

**Reservation Model**:
The booking pattern assigned to an equipment item.
_Avoid_: UI tab, file split

**Slot Reservation**:
A reservation made by choosing from predefined time slots.
_Avoid_: free-form timed booking

**Timed Reservation**:
A reservation made by selecting an arbitrary start time and end time.
_Avoid_: slot booking

**Cleanup Buffer**:
An optional period between reservations during which an equipment item cannot be booked.
_Avoid_: overlap rule, booking horizon

**Cancellation**:
An Approved User's action to release a reservation before its start time.
_Avoid_: no-show, expired reservation

**Check-In**:
An action that confirms a user has arrived to use a reservation.
_Avoid_: login, cancellation

**Rebooking**:
The act of creating a new reservation after cancelling an existing one.
_Avoid_: in-place edit, reservation mutation

**Reservation Status**:
The current lifecycle state of a reservation record.
_Avoid_: deletion, log-only event

**Scheduled**:
A Reservation Status for a reservation that is planned and not cancelled.
_Avoid_: draft, pending check-in

**Cancelled**:
A Reservation Status for a reservation that was released before it started.
_Avoid_: deleted reservation

**Completed**:
A Reservation Status for a reservation whose time window has finished without cancellation.
_Avoid_: checked in, archived

**Equipment Note**:
An advisory instruction shown to users about how an equipment item should be used.
_Avoid_: access rule, booking block

**PI**:
A principal investigator responsible for a research group whose members may request access.
_Avoid_: owner, admin

**Lecturer**:
A teaching staff member involved in authorizing access for eligible users.
_Avoid_: teacher, admin

**Sponsor**:
The PI or Lecturer who is named by an Applicant as the person responsible for approving access.
_Avoid_: referee, owner, admin

**Sponsor Directory**:
The lecturer list used to identify who is recognized as eligible for Sponsor Approval.
_Avoid_: free-text approver list, public faculty list

**Directory Manager**:
A trusted person allowed to maintain the Sponsor Directory.
_Avoid_: all sponsors, generic admin

**Operations Manager**:
A person allowed to manage day-to-day reservation operations without controlling sponsor or directory powers.
_Avoid_: super admin, sponsor manager

**Admin**:
A fallback role with the highest authority for recovery and system control.
_Avoid_: ordinary operations role, sponsor-only role

**Audit Log**:
An immutable history of important access, policy, and reservation events.
_Avoid_: editable activity note, deleted history

**Audit Reason**:
A short explanation required when a sensitive governance assignment is changed.
_Avoid_: silent privileged change, free-form essay

**Launch Notifications**:
The email notification types that must be sent at launch.
_Avoid_: optional nice-to-have alerts, silent state changes

**Capability Assignment**:
An independent permission granted to a person in addition to their User Category.
_Avoid_: single role string, account type

**Integrated Full-Stack App**:
A single deployable web application that serves the user interface and backend behavior together.
_Avoid_: split frontend/backend services, single-file script

**Application Stack**:
The implementation stack chosen for the Integrated Full-Stack App.
_Avoid_: legacy Streamlit script, ad hoc tooling mix

**Launch Platform**:
The managed hosting and service combination used to run the Integrated Full-Stack App at launch.
_Avoid_: Streamlit deployment, self-hosted server

**Legacy Migration**:
The selected scope for carrying data from the current Streamlit system into the rewrite.
_Avoid_: full blind import, fresh start without review

**Legacy-Imported History**:
Historical data brought into the rewrite with an explicit marker that it originated from the prior system.
_Avoid_: native record, current audit event

**Cutover Period**:
A short transition window in which the old and new systems both exist while the new system becomes the active one.
_Avoid_: indefinite dual operation, direct blind switch

## Relationships

- An **Applicant** must have a **KU Identity**
- **KU Email Verification** is weaker than a **KU Identity**
- **Fallback Identity** for launch can be based on **KU Email Verification**
- the launch **Fallback Identity** uses **One-Time Code Login**
- An **Applicant** creates one **Access Request**
- An **Access Request** moves through one of these **Access Request Status** values: **Pending**, **Approved**, **Denied**, or **Expired**
- changing the chosen **Sponsor** requires a new **Access Request**
- launch **Access Request Fields** are applicant full name, `@ku.th` email, chosen sponsor, suggested user category, and lab room number or department affiliation
- An **Applicant** becomes an **Approved User** only after **Access Approval**
- An **Approved User** receives **Booking Access** to all enabled equipment
- An **Approved User** keeps **Booking Access** only during the active **Access Term**
- **Lecturer** is an exception and keeps **Booking Access** until **Deactivation**
- A **User Category** determines the default **Access Term**
- a person has one **User Category** and can also hold multiple **Capability Assignments**
- A **User Category** can determine a **Booking Quota**
- A **User Category** can determine a **Booking Horizon**
- **Operations Manager** performs **Deactivation**
- **Operations Manager** can apply **Access Restriction** before **Deactivation**
- A **Reservation Policy** can vary by **User Category**
- launch **Access Restriction** can reduce **Booking Horizon**, max active future reservations, and max reservation duration
- `Undergraduate Student` default **Reservation Policy** is horizon 30 days, max 10 active future reservations, max duration 168 hours
- `Master Student` default **Reservation Policy** is horizon 30 days, max 15 active future reservations, max duration 168 hours
- `PhD Student` default **Reservation Policy** is horizon 30 days, max 15 active future reservations, max duration 168 hours
- `Research Assistant` default **Reservation Policy** is horizon 30 days, max 15 active future reservations, max duration 168 hours
- `Researcher` default **Reservation Policy** is horizon 45 days, max 15 active future reservations, max duration 168 hours
- `Lecturer` default **Reservation Policy** is horizon 60 days, max 20 active future reservations, max duration 168 hours
- An equipment item uses exactly one **Reservation Model**
- An equipment item can have an optional **Cleanup Buffer**
- A reservation can be ended early through **Cancellation** only before its start time
- **Check-In** is not required for a reservation to become active
- Reservation changes happen through **Cancellation** followed by **Rebooking**
- A reservation record is preserved and tracked through **Reservation Status**
- A reservation moves through one of these **Reservation Status** values: **Scheduled**, **Cancelled**, or **Completed**
- **Operations Manager** and **Admin** can create a **Delegated Reservation**, which must record who created it and on whose behalf
- **Operations Manager** and **Admin** can perform **Delegated Cancellation**, which must record who cancelled it and on whose behalf
- **Sponsor Capability** is separate from **User Category**
- An **Equipment Note** does not limit **Booking Access**
- A **PI** and a **Lecturer** are distinct roles
- A **Sponsor** is either a **PI** or a **Lecturer**
- A **Directory Manager** maintains the **Sponsor Directory**
- An **Operations Manager** manages operational controls without granting **Sponsor Capability**
- **Admin** is the fallback role with recovery authority above **Operations Manager**
- **Admin** can directly change high-trust assignments during recovery
- **Directory Manager** can directly change high-trust assignments except for the **Admin** role
- **Directory Manager** can change the **Lecturer** user category, **Sponsor Capability**, **Directory Manager**, and **Operations Manager**
- **Operations Manager** cannot change roles, capabilities, or user categories
- high-trust assignment changes by **Admin** or **Directory Manager** require an **Audit Reason** stored in the **Audit Log**
- exactly one named **Admin** account exists at launch
- the launch **Admin** cannot be deactivated through ordinary in-app controls
- the launch **Admin** is also a normal person record with explicit **Capability Assignments**
- the launch **Admin** is bootstrap-defined and not reassigned through ordinary in-app controls
- the rewrite is delivered as one **Integrated Full-Stack App**
- the launch **Application Stack** is Next.js, Postgres, Prisma, and Auth.js
- the launch **Launch Platform** is Vercel, Neon, and Resend
- **Legacy Migration** includes the equipment catalog, enabled status, future reservations, and reliably matched approved users
- imported historical reservations are preserved as **Legacy-Imported History**
- reliably matched imported approved users keep access after one **KU Email Verification**
- unmatched legacy users are treated as new **Applicants**
- the launch uses a short **Cutover Period**, but only the new system accepts new approvals and new reservations
- the launch requires email notifications for one-time code login, access request submitted, sponsor approval request, access approved, access denied, access request expired, access renewal reminder, access expired, reservation created, reservation cancelled, and delegated reservation or cancellation affecting a user
- important operational and access events are preserved in the **Audit Log**
- An **Applicant** names exactly one **Sponsor** when requesting access
- A **Sponsor** decides the outcome of an **Access Request**
- **Access Approval** is granted through **Sponsor Approval**
- **Sponsor Approval** cannot be delegated to **Operations Manager** or **Admin**
- all **Lecturer** users automatically receive **Sponsor Capability**
- the **Sponsor Directory** identifies recognized lecturers for sponsor selection
- only **Directory Manager** or **Admin** can assign the **Lecturer** user category
- a **Sponsor** assigns ordinary **User Category** values during **Sponsor Approval**
- an **Applicant** can suggest a **User Category**, but the **Sponsor** confirms or changes it during approval
- a **Sponsor** sees only their own pending and past approval decisions, plus the minimum applicant details needed to decide
- an **Operations Manager** sees all reservations, all current users, active restrictions, equipment availability, and announcements
- an **Operations Manager** also has read-only access to all **Access Request** records for troubleshooting
- **Admin** has full visibility and override authority across users, access requests, reservations, restrictions, sponsor data, announcements, and audit history

## Example dialogue

> **Dev:** "If someone signs in with a **KU Identity**, are they immediately an **Approved User**?"
> **Domain expert:** "No — they first become an **Applicant**, and only gain access after **Access Approval**."

## Flagged ambiguities

- "login" was used to mean both proving a **KU Identity** and being allowed to reserve equipment — resolved: identity and access are separate steps.
- "`@ku.th` login" could mean either true institutional authentication or only inbox proof — resolved: **KU Email Verification** is not the same as a **KU Identity**.
- "register" was used to mean both account creation and approval to use laboratory equipment — resolved: access depends on **Access Approval**, not open signup.
- "launch identity" could have blocked on university IT support — resolved: if KU SSO is unavailable, the launch **Fallback Identity** is restricted to verified `@ku.th` email access.
- "passwordless login" could still have meant multiple email flows — resolved: the launch auth method is **One-Time Code Login**.
- "approval email" could have been treated as sufficient proof of sponsor identity — resolved: **Sponsor Approval** requires the Sponsor to sign in from their own verified `@ku.th` account.
- "request state" could have been conflated with booking or user state — resolved: **Access Request** uses exactly **Pending**, **Approved**, **Denied**, and **Expired**.
- "wrong sponsor" could have implied editing a pending request — resolved: changing the chosen **Sponsor** requires a new **Access Request**.
- "what information belongs in access onboarding" is resolved for launch through explicit **Access Request Fields**.
- "why do you need access" is not collected at launch; sponsor recognition is considered sufficient for approval context.
- "what a sponsor can see" is resolved narrowly through **Sponsor View**: only their own requests and past decisions, with minimum applicant detail.
- "what operations can see" is resolved through **Operations View**: broad operational visibility without automatic sponsor-decision authority.
- "operations troubleshooting" is supported through read-only visibility of all **Access Request** records.
- "sponsor decision substitution" is not allowed — resolved: **Sponsor Approval** cannot be delegated to **Operations Manager** or **Admin**.
- "recovery authority" includes direct assignment changes: **Admin** can change high-trust assignments, and **Directory Manager** can do the same except for the **Admin** role.
- "**Directory Manager** assignment scope is explicit: **Lecturer** user category, **Sponsor Capability**, **Directory Manager**, and **Operations Manager**."
- "**Operations Manager** is governance-blind: it cannot change roles, capabilities, or user categories."
- "sensitive governance changes" require explicit accountability — resolved: **Admin** and **Directory Manager** must provide an **Audit Reason** stored in the **Audit Log**.
- "fallback admin" is a real recovery authority, not a symbolic title — resolved through full **Admin Override**.
- "manual help booking" is supported through **Delegated Reservation**, with explicit attribution in the record.
- "manual help cancellation" is supported through **Delegated Cancellation**, with explicit attribution in the record.
- "**Lecturer** is the exception to the normal **Access Term** model and keeps access until **Deactivation**; the remaining unresolved detail is which role has deactivation authority."
- "PI or lecturer" was used as free text for the approver role — resolved: the canonical term is **Sponsor**.
- "approval" could have meant sponsor endorsement plus later staff review — resolved: **Sponsor Approval** is the final gate.
- "real sponsor" could have been checked by email text alone — resolved: Sponsors are validated through KU login and lecturer recognition in the **Sponsor Directory**.
- "who can be a sponsor" is resolved narrowly: at launch, all **Lecturer** users automatically receive **Sponsor Capability**.
- "`Lecturer` is a high-trust classification: only **Directory Manager** or **Admin** can assign that **User Category**."
- "ordinary user classification" is resolved operationally: the **Sponsor** assigns non-lecturer **User Category** values during approval.
- "applicant category" is not final truth — resolved: the **Applicant** suggests a **User Category**, and the **Sponsor** confirms or changes it.
- "equipment access" could have meant a per-equipment permission model — resolved for now: an **Approved User** gets **Booking Access** to all enabled equipment.
- "contact before use" could have implied an enforced restriction — resolved for now: that is an **Equipment Note**, not a booking rule.
- "approval request" needed an operational path — resolved: the canonical workflow starts with an **Access Request** tied to one **Sponsor**.
- "approved once" could have implied lifelong access — resolved: approval is bounded by an **Access Term** and must be renewed.
- "**Lecturer** is the explicit exception to renewable access and keeps access until **Deactivation**."
- "renewal" could have meant the same duration for everyone — resolved: default **Access Term** is determined by **User Category**.
- "Lecturer" is used in two ways — resolved by separating **User Category** from **Sponsor Capability**.
- "who can approve applicants" and "who can manage sponsors" could have been the same power — resolved: **Directory Manager** is separate from **Sponsor Capability**.
- "operations admin" could have implied full trust-management power — resolved: **Operations Manager** is a narrow operational role only.
- "history" could have meant editable logs or disappearing rows — resolved: important events are preserved in an immutable **Audit Log**.
- "role" could have implied one mutually exclusive label per person — resolved: **User Category** and operational powers are separate, and powers are modeled as **Capability Assignments**.
- "same real person" could have implied automatic power inheritance — resolved: **Sponsor Capability** and **Operations Manager** remain separately assigned **Capability Assignments**.
- "who can remove access" is resolved: **Operations Manager** performs **Deactivation**.
- "abuse response" is resolved: **Operations Manager** can apply **Access Restriction** before **Deactivation**.
- "manual restriction" is resolved for launch: it can reduce **Booking Horizon**, max active future reservations, and max reservation duration, but not add per-equipment bans yet.
- "operations recovery" could have depended on the current operator never making mistakes — resolved: the system has a fallback **Admin** role with the highest authority.
- "fallback admin" could have expanded into a broad admin group — resolved: exactly one named **Admin** account exists at launch.
- "fallback admin" could still have been vulnerable to routine operational mistakes — resolved: the launch **Admin** is protected from ordinary in-app deactivation.
- "admin account" could have become a separate ghost identity — resolved: the launch **Admin** is a normal person record with explicit elevated capabilities.
- "highest privilege reassignment" could have become a routine UI action — resolved: the launch **Admin** is bootstrap-only at first.
- "production rewrite" could have been split into multiple services too early — resolved: launch uses one **Integrated Full-Stack App**.
- "rewrite stack" could have remained open-ended — resolved: the launch **Application Stack** is Next.js, Postgres, Prisma, and Auth.js.
- "managed deployment" could still have remained abstract — resolved: the launch **Launch Platform** is Vercel, Neon, and Resend.
- "migration" could have implied a full blind carryover from weak CSV records — resolved: **Legacy Migration** is selective and reliability-driven.
- "imported history" could have been mistaken for native audited data — resolved: old historical reservations are marked as **Legacy-Imported History**.
- "imported approved user" could have implied silent trust carryover — resolved: reliably matched imported users keep access only after one **KU Email Verification**.
- "unmatched legacy user" could have implied temporary silent trust — resolved: unmatched legacy users re-enter through the normal **Applicant** path.
- "parallel run" could have implied long-term dual-write complexity — resolved: the launch uses a short **Cutover Period** and only the new system accepts new approvals and reservations.
- "conservative quota" is resolved for launch by explicit per-category defaults, even though those limits are relatively generous for long-duration equipment use.
- "`168 hours` looked like an exception-only duration, but for launch it is intentionally the default max duration for all **Timed Reservation** equipment because some equipment may need multi-day or week-long runs; tighter per-equipment limits can be introduced later if abuse appears."
- "which emails are mandatory" is resolved through **Launch Notifications**.
- "booking limits" could have meant both quantity and lead time — resolved: use **Booking Quota** for capacity limits and **Booking Horizon** for how far ahead booking is allowed.
- "reservation rules" could have stayed scattered across UI branches — resolved: the canonical concept is a **Reservation Policy**.
- "PCR vs non-PCR" could have stayed an implementation-only split — resolved: the domain uses distinct **Reservation Models**: **Slot Reservation** and **Timed Reservation**.
- "no overlap" could have been mistaken for "no operational gap" — resolved: back-to-back use is allowed by default, with optional per-equipment **Cleanup Buffer** later.
- "missed booking" could have implied a tracked enforcement concept — resolved for now: the system supports **Cancellation** before start time but does not model no-show detection.
- "active reservation" could have implied arrival confirmation — resolved: **Check-In** is not part of the launch model.
- "edit reservation" could have implied mutable bookings — resolved: reservation changes are handled through **Rebooking**, not in-place edits.
- "cancelled booking" could have implied row deletion — resolved: reservations are preserved and tracked by **Reservation Status**.
- "reservation state" could have proliferated into operationally noisy states — resolved: the launch lifecycle uses exactly **Scheduled**, **Cancelled**, and **Completed**.
