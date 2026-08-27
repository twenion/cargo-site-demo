/**
 * Shared data for the demo.
 *
 * The tariff table and the calculator read the same numbers from here, so the
 * price a visitor is quoted can never disagree with the price on the tariff
 * page -- a mismatch between the two is exactly the kind of thing that costs a
 * real courier a customer.
 */
window.XE = window.XE || {};

/* Base covers the first kilogram; every kilo after that is charged at perKg. */
window.XE.tariffs = {
  destinations: [
    {
      id: "baku",
      label: "Bakı (şəhərdaxili)",
      base: 5.5,
      perKg: 1.0,
      duration: "Eyni gün",
      note: "Saat 14:00-a qədər verilən sifarişlər",
    },
    {
      id: "sumqayit",
      label: "Sumqayıt / Abşeron",
      base: 7.0,
      perKg: 1.2,
      duration: "Eyni gün / ertəsi gün",
      note: "Axşam 17:00-dək qəbul",
    },
    {
      id: "region-yaxin",
      label: "Yaxın regionlar",
      base: 9.5,
      perKg: 1.6,
      duration: "24 saat",
      note: "Gəncə, Şəki, Quba, Şirvan",
    },
    {
      id: "region-uzaq",
      label: "Uzaq regionlar",
      base: 13.0,
      perKg: 2.1,
      duration: "48 saat",
      note: "Lənkəran, Zaqatala, Naxçıvan",
    },
  ],
  /* Picking the parcel up outside Baku adds a leg to the route. */
  originSurcharge: { baku: 1, sumqayit: 1.1, gence: 1.15 },
  urgentMultiplier: 1.5,
  maxWeightKg: 500,
};

/* Three sample shipments so the tracking page has something honest to show.
   The footer states plainly that these are made up. */
window.XE.shipments = {
  XE4827193: {
    status: "yolda",
    from: "Bakı, Nizami küçəsi 118",
    to: "Gəncə, Atatürk prospekti 42",
    weight: 4.5,
    service: "Regionlara çatdırılma",
    estimate: "29.08.2026",
    events: [
      { date: "27.08.2026 09:14", place: "Bakı, mərkəzi anbar", text: "Yük qəbul edildi" },
      { date: "27.08.2026 11:40", place: "Bakı, mərkəzi anbar", text: "Çeşidləmə tamamlandı" },
      { date: "27.08.2026 15:22", place: "Bakı → Gəncə", text: "Yola salındı" },
    ],
  },
  XE1029384: {
    status: "catdirilib",
    from: "Bakı, 28 May küçəsi 7",
    to: "Bakı, Xətai rayonu, Babək prospekti 12",
    weight: 1.2,
    service: "Şəhərdaxili kuryer",
    estimate: "26.08.2026",
    events: [
      { date: "26.08.2026 10:02", place: "Bakı, 28 May", text: "Kuryer yükü götürdü" },
      { date: "26.08.2026 12:35", place: "Bakı, Xətai", text: "Çatdırılma marşrutunda" },
      { date: "26.08.2026 14:08", place: "Bakı, Xətai", text: "Alıcıya təhvil verildi" },
    ],
  },
  XE5560271: {
    status: "qebul",
    from: "Sumqayıt, Sülh küçəsi 3",
    to: "Lənkəran, Həzi Aslanov küçəsi 55",
    weight: 12,
    service: "Yük daşıma",
    estimate: "30.08.2026",
    events: [
      { date: "27.08.2026 16:45", place: "Sumqayıt, qəbul məntəqəsi", text: "Yük qəbul edildi" },
    ],
  },
};

window.XE.statusLabels = {
  qebul: { text: "Qəbul edildi", tone: "wait" },
  yolda: { text: "Yoldadır", tone: "move" },
  catdirilib: { text: "Çatdırıldı", tone: "done" },
};
