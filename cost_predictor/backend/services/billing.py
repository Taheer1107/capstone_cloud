from services import diagnostics_service
from services import medicine_service
from services import consumable_service


class Billing:

    def __init__(self):

        self.procedure_cost = 0

        self.diagnostics = []

        self.medicines = []

        self.consumables = []

        self.other_charges = []

    # =====================================================
    # PROCEDURE COST
    # =====================================================

    def set_procedure_cost(self, cost):

        self.procedure_cost = float(cost)

    # =====================================================
    # DIAGNOSTICS
    # =====================================================

    def add_diagnostic(self, diagnostic_id, quantity):

        diagnostic = diagnostics_service.get_diagnostic(
            diagnostic_id
        )

        if diagnostic is None:
            raise ValueError(
                f"Diagnostic ID '{diagnostic_id}' not found."
            )

        subtotal = diagnostic["unit_price"] * quantity

        self.diagnostics.append({

            "diagnostic_id": diagnostic["diagnostic_id"],

            "procedure_name": diagnostic["procedure_name"],

            "quantity": quantity,

            "unit_price": diagnostic["unit_price"],

            "subtotal": subtotal

        })

    # =====================================================
    # MEDICINES
    # =====================================================

    def add_medicine(self, medicine_id, quantity):

        medicine = medicine_service.get_medicine(
            medicine_id
        )

        if medicine is None:
            raise ValueError(
                f"Medicine ID '{medicine_id}' not found."
            )

        subtotal = medicine["unit_price"] * quantity

        self.medicines.append({

            "medicine_id": medicine["medicine_id"],

            "generic_name": medicine["generic_name"],

            "quantity": quantity,

            "unit_price": medicine["unit_price"],

            "subtotal": subtotal

        })

    # =====================================================
    # CONSUMABLES
    # =====================================================

    def add_consumable(self, consumable_id, quantity):

        consumable = consumable_service.get_consumable(
            consumable_id
        )

        if consumable is None:
            raise ValueError(
                f"Consumable ID '{consumable_id}' not found."
            )

        subtotal = (
            consumable["unit_price"]
            * quantity
        )

        self.consumables.append({

            "consumable_id": consumable["consumable_id"],

            "item_name": consumable["item_name"],

            "quantity": quantity,

            "unit_price": consumable["unit_price"],

            "subtotal": subtotal

    })

    # =====================================================
    # OTHER CHARGES
    # =====================================================

    def add_other_charge(self, name, amount):

        self.other_charges.append({

            "name": name,

            "amount": float(amount)

        })

    # =====================================================
    # TOTALS
    # =====================================================

    def diagnostics_total(self):

        return sum(
            item["subtotal"]
            for item in self.diagnostics
        )

    def medicines_total(self):

        return sum(
            item["subtotal"]
            for item in self.medicines
        )

    def consumables_total(self):

        return sum(
            item["subtotal"]
            for item in self.consumables
        )

    def other_total(self):

        return sum(
            item["amount"]
            for item in self.other_charges
        )

    # =====================================================
    # GRAND TOTAL
    # =====================================================

    def gross_bill(self):

        return (

            self.procedure_cost

            + self.diagnostics_total()

            + self.medicines_total()

            + self.consumables_total()

            + self.other_total()

        )

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):

        return {

            "procedure_cost": self.procedure_cost,

            "diagnostics": self.diagnostics,

            "diagnostics_total": self.diagnostics_total(),

            "medicines": self.medicines,

            "medicines_total": self.medicines_total(),

            "consumables": self.consumables,

            "consumables_total": self.consumables_total(),

            "other_charges": self.other_charges,

            "other_total": self.other_total(),

            "gross_bill": self.gross_bill()

        }