/** @odoo-module **/

const modeRegistry = new Map();

function normalizeMode(mode) {
    if (!mode?.key) {
        throw new Error("AdventurePOS modes require a unique key.");
    }
    if (!mode.label) {
        throw new Error(`AdventurePOS mode "${mode.key}" requires a label.`);
    }
    return {
        sequence: 100,
        isAvailable: () => true,
        ...mode,
    };
}

export function registerAdventurePOSMode(mode) {
    const normalized = normalizeMode(mode);
    if (modeRegistry.has(normalized.key)) {
        console.warn(`AdventurePOS mode "${normalized.key}" was already registered; replacing it.`);
    }
    modeRegistry.set(normalized.key, normalized);
    return normalized;
}

export function getAdventurePOSModes(env, pos) {
    return [...modeRegistry.values()]
        .filter((mode) => !mode.isAvailable || mode.isAvailable(env, pos))
        .sort((left, right) => (left.sequence || 100) - (right.sequence || 100));
}

export function getAdventurePOSMode(key) {
    return modeRegistry.get(key);
}

export function getAdventurePOSState(pos) {
    if (!pos.adventurePOSState) {
        pos.adventurePOSState = { activeMode: "sale" };
    }
    return pos.adventurePOSState;
}

export function setAdventurePOSMode(pos, key) {
    const mode = getAdventurePOSMode(key);
    if (!mode) {
        console.warn(`AdventurePOS mode "${key}" is not registered.`);
        return false;
    }
    getAdventurePOSState(pos).activeMode = key;
    return true;
}

// Vertical modules can import registerAdventurePOSMode and add their own modes.
// For example, dive_shop_pos can register fill_station, tank_inspection, and service_queue.
registerAdventurePOSMode({
    key: "sale",
    label: "Sale",
    icon: "fa-shopping-cart",
    sequence: 10,
    component: null,
});
