/** @odoo-module **/

export const RENTAL_STATES = Object.freeze({
    available: "success",
    reserved: "info",
    assigned: "info",
    checked_out: "warning",
    returned: "success",
    overdue: "danger",
    damaged: "danger",
    maintenance_due: "warning",
});

export function rentalStateClass(state) {
    return RENTAL_STATES[state] || "secondary";
}

export function formatRentalLine(config) {
    const pickup = formatRentalDate(config.pickupDate);
    const returns = formatRentalDate(config.returnDate);
    const deposit = Number(config.deposit || 0).toFixed(2);
    return `${pickup} -> ${returns}\nDeposit: $${deposit}`;
}

export function formatRentalDate(value) {
    if (!value) {
        return "";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export const sampleReservations = [
    {
        id: "R-1042",
        customer: "Maya Carter",
        product: "Full Scuba Kit",
        pickup: "2026-05-01T09:00",
        returns: "2026-05-03T17:00",
        qty: 1,
        state: "reserved",
        requirements: ["Waiver signed", "Open Water certification", "Deposit authorized"],
    },
    {
        id: "R-1043",
        customer: "Jon Ellis",
        product: "BCD + Regulator",
        pickup: "2026-05-01T11:30",
        returns: "2026-05-02T16:00",
        qty: 2,
        state: "assigned",
        requirements: ["Certification pending", "Inspection current"],
    },
];

export const sampleActiveRentals = [
    {
        id: "CO-8102",
        customer: "Nora Singh",
        product: "Full Scuba Kit",
        due: "2026-05-01T16:00",
        asset: "KIT-204",
        state: "checked_out",
        fees: [{ label: "Air fill", amount: 12 }],
    },
    {
        id: "CO-8098",
        customer: "Luis Romero",
        product: "Dive Computer",
        due: "2026-04-30T17:00",
        asset: "DC-118",
        state: "overdue",
        fees: [{ label: "Late", amount: 35 }],
    },
];
