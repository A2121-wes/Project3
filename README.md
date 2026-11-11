# BoilerBite — Project 3 nutrition dashboard

## Publish with GitHub Pages

1. In your `A2121-wes/Project3` repo, upload **`index.html`** and **`menu.csv`** to the root of the `main` branch. Upload the contents of this folder, not the containing folder.
2. Settings → Pages → Deploy from a branch → `main` → `/(root)` → Save.
3. Open `https://a2121-wes.github.io/Project3/` once deployed. Hard-refresh if you still see the old version.
4. `menu.csv` will load automatically from the *same folder as the HTML*. You can upload a new CSV using the in-page upload field. GitHub Pages cannot execute `purdue_dining_daily.py`; update the CSV each day manually or automate it with GitHub Actions.

## Serving-size support

Uses labels from Purdue CSV, including **1/2 Cup, 1/3 Cup, 1/4 Cup, 3/4 Cup, Each, 2 Each Serving, 2 Piece Serving, 4 Per Serving, Slice, Bun, Burger, Egg, Roll, Bagel, Muffin, Brownie, Cookie, Tortilla, Teaspoon, Tablespoon, Ounce, 4 oz Serving, 6 oz Ladle, Serving, Chicken Thigh, 8x10 Cut Serving, 4x8 Cut Serving**, and fallback to the original label for unknown serving types.

In **Enter cups/pieces/servings**, choose an item and type the amount in the published unit. E.g. nutrition for `1/2 cup` is multiplied by two if the amount eaten is `1 cup`. For `2 Each Serving`, entering `1 piece` gives half of the published nutrients.

In **Measure with scale**, calculate grams from a known gram-serving amount. If Purdue gives a mass serving (e.g. 4 oz) it auto-converts to grams. Cups, ladles, pieces, cuts and serving-size labels without a mass **cannot be converted automatically from grams**, as density and portion size vary by food. Weigh one published serving of that food and enter its measured grams in **Grams for one published serving**. Calibration is remembered per food in this browser.

## Sensor: your current MicroPython (`main.py` + hx711.py)

Your `main.py` writes `val = ... weight = 123.4 g` to **USB serial**, not Bluetooth. On **desktop Chrome/Edge**, connect the micro:bit using a data USB cable, open this HTTPS website and select **USB serial**. The dashboard parses the existing `weight = X g` lines directly. USB serial generally isn't available in iPhone Safari. Adjust the baud rate on the webpage if your firmware differs from 115200.

The website works on *tray weight changes*: click **Set tray baseline** with the tray before a serving, then remove food. The difference is how many grams were taken. Choose a food and ID first. You can manually click **Log measured serving**, or turn on **Auto-log stable weight drops** when ready.

## Bluetooth HX711: MakeCode JavaScript

For wireless Bluetooth, compile `microbit_makecode_bluetooth.ts` in MakeCode JavaScript. Add MakeCode extensions `bluetooth` and `github:daferdur/pxt-myHX711`. Use the same P2/P1 wiring. When connected, it sends `W,123.4` over BLE micro:bit UART twice a second. **This is a port of your sensor idea to MakeCode; it is not your existing MicroPython code running over Bluetooth.** The HX711 extension and calibration must be tested on your hardware.

If Bluetooth connection fails, enable MakeCode **No Pairing Required** for testing and reflash. Web Bluetooth works with supported Chrome/Edge browsers (e.g. desktop Chrome and Android Chrome), not iPhone Safari.

## Logs and safety

Records are stored in the browser localStorage by *anonymous ID*, not synced across users/devices and not a secure sign-in system. Export is available as CSV. The uploaded CSV includes **ingredients**, but not confirmed dietary tags/allergens. The page warns about this, rather than guessing. Check with Purdue Dining for allergen safety.
