/* Holiday gift guide. Shows between "start" and "end" (YYYY-MM-DD, your visitors' local date).
   Each item links to a tagged Amazon search. Swap any "q" for a "url" with a direct product
   link (SiteStripe) when you have one, e.g. { title: "...", url: "https://www.amazon.com/dp/..." }. */
window.GIFT_GUIDE = {
  title: "Malfoid's Gift Guide",
  intro: "Gifts worthy of the Manor. I've done the choosing, you do the wrapping.",
  start: "2026-11-01",
  end: "2026-12-25",
  sections: [
    { name: "Stocking Stuffers", note: "Small, clever, very giftable", items: [
      { title: "Enamel Pins", q: "harry potter enamel pins" },
      { title: "House Socks", q: "harry potter socks" },
      { title: "Keychains", q: "harry potter keychain" },
      { title: "Every Flavour Beans", q: "bertie botts beans" } ] },
    { name: "For the Slytherin", note: "Emerald, silver, superior", items: [
      { title: "Slytherin Scarf", q: "slytherin scarf" },
      { title: "Slytherin Robe", q: "slytherin robe adult" },
      { title: "Slytherin Mug", q: "slytherin mug" },
      { title: "Slytherin Hoodie", q: "slytherin hoodie" } ] },
    { name: "For the Collector", note: "Shelf-worthy treasures", items: [
      { title: "Character Wands", q: "harry potter wand noble collection" },
      { title: "Golden Snitch", q: "golden snitch replica" },
      { title: "Funko Pop!", q: "harry potter funko pop" },
      { title: "Illustrated Editions", q: "harry potter illustrated edition" } ] },
    { name: "Big Gifts", note: "For someone very, very good this year", items: [
      { title: "Hogwarts Castle LEGO", q: "lego harry potter hogwarts castle" },
      { title: "Interactive Wand", q: "harry potter interactive wand" },
      { title: "Marauder's Map", q: "marauders map replica" },
      { title: "LEGO Advent Calendar", q: "lego harry potter advent calendar" } ] }
  ]
};
