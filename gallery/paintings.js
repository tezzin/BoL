// ============================================================
//  EDIT THIS FILE to set up your gallery.
//  1. Change the SITE settings (your name, email, bio).
//  2. Put your painting photos in the "images" folder.
//  3. Add one entry per painting to the PAINTINGS list.
// ============================================================

const SITE = {
  artistName: "Your Name",
  tagline: "Original paintings, made by hand.",
  // Buyers' inquiries open an email addressed here:
  email: "you@example.com",
  currency: "USD",
  about:
    "I paint with oils and acrylics, mostly abstract landscapes and color studies. " +
    "Every piece here is an original, signed on the back, and ships ready to hang. " +
    "Get in touch if you'd like to buy something or ask about a commission.",
  instagram: "", // e.g. "https://instagram.com/yourname" (leave empty to hide)
};

// status: "available", "reserved", or "sold"
const PAINTINGS = [
  {
    id: "harbor-at-dusk",
    title: "Harbor at Dusk",
    year: 2025,
    medium: "Oil on canvas",
    size: "40 × 50 cm",
    price: 450,
    status: "available",
    image: "images/painting-1.svg",
    description: "Cool blues settling over the water just after sunset.",
  },
  {
    id: "desert-heat",
    title: "Desert Heat",
    year: 2025,
    medium: "Acrylic on canvas",
    size: "60 × 48 cm",
    price: 620,
    status: "available",
    image: "images/painting-2.svg",
    description: "Warm ochres and terracotta layered in loose, fast strokes.",
  },
  {
    id: "garden-study",
    title: "Garden Study",
    year: 2024,
    medium: "Oil on board",
    size: "30 × 30 cm",
    price: 280,
    status: "sold",
    image: "images/painting-3.svg",
    description: "A small, quiet study of a summer garden in soft light.",
  },
  {
    id: "night-signal",
    title: "Night Signal",
    year: 2025,
    medium: "Acrylic on canvas",
    size: "50 × 70 cm",
    price: 700,
    status: "available",
    image: "images/painting-4.svg",
    description: "Deep navy with a single warm light cutting through.",
  },
  {
    id: "earth-tones",
    title: "Earth Tones",
    year: 2024,
    medium: "Oil on canvas",
    size: "70 × 50 cm",
    price: 750,
    status: "reserved",
    image: "images/painting-5.svg",
    description: "Browns and sage greens inspired by autumn walks.",
  },
  {
    id: "lavender-hour",
    title: "Lavender Hour",
    year: 2025,
    medium: "Oil on canvas",
    size: "45 × 45 cm",
    price: 480,
    status: "available",
    image: "images/painting-6.svg",
    description: "Muted violets and blush pinks, calm and meditative.",
  },
  {
    id: "carnival",
    title: "Carnival",
    year: 2023,
    medium: "Acrylic on paper",
    size: "40 × 50 cm",
    price: 320,
    status: "sold",
    image: "images/painting-7.svg",
    description: "Bright reds and oranges full of movement and noise.",
  },
  {
    id: "red-line",
    title: "Red Line",
    year: 2025,
    medium: "Mixed media on canvas",
    size: "80 × 60 cm",
    price: 900,
    status: "available",
    image: "images/painting-8.svg",
    description: "Grey calm interrupted by a sharp streak of red.",
  },
];
