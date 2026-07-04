import { useEffect, useMemo, useState } from "react";

const compartmentImagePaths = Array.from({ length: 24 }, (_value, index) => {
  const number = String(index + 1).padStart(3, "0");
  return `/images/bt_slides/BT.${number}.png`;
});

const previewImagePaths = [
  "/images/bt_slides/BT.001.png",
  "/images/bt_slides/BT.004.png",
  "/images/bt_slides/BT.008.png",
  "/images/bt_slides/BT.012.png",
  "/images/bt_slides/BT.016.png",
  "/images/bt_slides/BT.020.png",
  "/images/bt_slides/BT.024.png",
  "/images/bt_slides/Twist.png",
];

const featureTags = ["Polish", "Twist", "Rhythm Clock", "POVs"];

export default function BasetrueCoverSlide() {
  const [activeIndex, setActiveIndex] = useState(0);
  const totalSlides = compartmentImagePaths.length;

  const activeImage = useMemo(() => {
    return compartmentImagePaths[activeIndex] || compartmentImagePaths[0];
  }, [activeIndex]);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((current) => (current + 1) % totalSlides);
    }, 2800);

    return () => clearInterval(timer);
  }, [totalSlides]);

  const goPrevious = () => {
    setActiveIndex((current) => (current - 1 + totalSlides) % totalSlides);
  };

  const goNext = () => {
    setActiveIndex((current) => (current + 1) % totalSlides);
  };

  return (
    <section className="bt-cover-slide" aria-label="Basetrue cover slide">
      <div className="bt-cover-hero">
        <img src={activeImage} alt={`Basetrue compartment ${activeIndex + 1}`} />
        <div className="bt-cover-controls" aria-label="Basetrue cover controls">
          <button type="button" className="bt-cover-nav" onClick={goPrevious}>
            Previous
          </button>
          <span className="bt-cover-counter">{activeIndex + 1} / {totalSlides}</span>
          <button type="button" className="bt-cover-nav" onClick={goNext}>
            Next
          </button>
        </div>
      </div>
      <div className="bt-cover-meta" aria-label="Basetrue cover metadata">
        <span className="bt-cover-pill">24 Basetrue Compartments</span>
        <span className="bt-cover-pill">{compartmentImagePaths.length} mapped visuals</span>
        {featureTags.map((tag) => (
          <span key={tag} className="bt-cover-pill bt-cover-pill-feature">
            {tag}
          </span>
        ))}
      </div>
      <div className="bt-cover-preview-grid" aria-label="Basetrue preview image strip">
        {previewImagePaths.map((path, index) => (
          <figure key={path} className="bt-cover-preview-card">
            <img src={path} alt={`Basetrue preview ${index + 1}`} loading="lazy" />
          </figure>
        ))}
      </div>
    </section>
  );
}