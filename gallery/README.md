# Painting Gallery

A simple website for showing and selling your paintings. It's plain HTML, CSS and JavaScript, so there's nothing to install or build.

## Adding your paintings

1. Take a photo of each painting (good daylight, straight on, cropped to the edges). JPG is fine; about 1600px on the long side is plenty.
2. Put the photos in the `images/` folder, e.g. `images/sunset.jpg`.
3. Open `paintings.js` and:
   - set your name, email, tagline, bio and (optionally) Instagram in `SITE`
   - replace the example entries in `PAINTINGS` with your own. Each needs a title, year, medium, size, price, status (`available`, `reserved` or `sold`), image path and a short description.
4. Delete the example `images/painting-*.svg` files once you've replaced them.

## Previewing

Double-click `index.html` to open it in your browser.

## How selling works

Each painting has an **Inquire** button that opens an email to you, with the painting's name and price already filled in. You then reply with shipping and payment details (bank transfer, PayPal, Vipps, etc.). When something sells, change its `status` to `"sold"`. It stays in the gallery marked as sold, which shows buyers that your work sells.

If you later want visitors to pay directly on the site, you can add a Stripe Payment Link (or PayPal button) per painting.

## Putting it online for free

**GitHub Pages:** in the repository go to *Settings → Pages*, pick this branch, and the site will be at `https://<username>.github.io/<repo>/gallery/`.

**Netlify Drop:** drag the `gallery` folder onto https://app.netlify.com/drop.
