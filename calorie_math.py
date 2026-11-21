"""Calorie Math: daily calorie needs (Mifflin-St Jeor), macro calories and protein/fiber targets inside Sublime Text.
Formulas and sources: https://snowbelly.app/tools/calorie-calculator/"""
import sublime
import sublime_plugin

ACTIVITY = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "very active": 1.725, "extra active": 1.9}


def bmr(kg, cm, age, sex):
    return 10 * kg + 6.25 * cm - 5 * age + (5 if sex == "male" else -161)


def macro_calories(protein, carbs, fat, alcohol=0.0):
    return 4 * protein + 4 * carbs + 9 * fat + 7 * alcohol


def _numbers(text, n):
    parts = [p for p in text.replace(",", " ").split() if p]
    if len(parts) < n:
        raise ValueError("expected %d values" % n)
    return parts


class CalorieMathTdeeCommand(sublime_plugin.WindowCommand):
    """Ask for weight (kg), height (cm), age, sex and activity; show BMR and TDEE."""

    def run(self):
        self.window.show_input_panel("weight_kg height_cm age sex(female/male):", "70 170 30 female", self.on_body, None, None)

    def on_body(self, text):
        try:
            w, h, a, s = _numbers(text, 4)[:4]
            self.body = (float(w), float(h), float(a), s.lower())
        except ValueError as e:
            sublime.error_message("Calorie Math: %s" % e)
            return
        names = list(ACTIVITY.keys())
        self.window.show_quick_panel(["%s (x%s)" % (k, v) for k, v in ACTIVITY.items()], lambda i: i >= 0 and self.show(names[i]))

    def show(self, level):
        w, h, a, s = self.body
        b = bmr(w, h, a, s)
        t = b * ACTIVITY[level]
        msg = "BMR %d kcal/day | TDEE %d kcal/day (%s) | gentle loss %d kcal/day | protein RDA %d g/day" % (
            round(b), round(t), level, round(max(t - 500, 1500 if s == "male" else 1200)), round(0.8 * w))
        sublime.message_dialog("Calorie Math (Mifflin-St Jeor)\n\n" + msg.replace(" | ", "\n") + "\n\nEstimates only, not medical advice.")


class CalorieMathMacrosCommand(sublime_plugin.WindowCommand):
    """Calories and percentage split from grams of protein, carbs and fat."""

    def run(self):
        self.window.show_input_panel("protein_g carbs_g fat_g:", "30 50 15", self.done, None, None)

    def done(self, text):
        try:
            p, c, f = [float(x) for x in _numbers(text, 3)[:3]]
        except ValueError as e:
            sublime.error_message("Calorie Math: %s" % e)
            return
        k = macro_calories(p, c, f)
        split = "protein %d%%, carbs %d%%, fat %d%%" % (round(400 * p / k), round(400 * c / k), round(900 * f / k)) if k else ""
        sublime.status_message("Calorie Math: %d kcal (%s)" % (round(k), split))


class CalorieMathInsertLabelCommand(sublime_plugin.TextCommand):
    """Insert a Markdown Nutrition Facts table to fill in."""

    def run(self, edit):
        table = ("| Nutrition Facts | per serving | % DV |\n|---|---:|---:|\n| Calories |  |  |\n| Total Fat |  g |  |\n"
                 "| Sodium |  mg |  |\n| Total Carbohydrate |  g |  |\n| Dietary Fiber |  g |  |\n| Total Sugars |  g |  |\n| Protein |  g |  |\n")
        for r in self.view.sel():
            self.view.insert(edit, r.begin(), table)
