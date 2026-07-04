export type CTAFooterProps = {
  headline: string;
  subline: string;
  buttonLabel: string;
  onClick: () => void;
};

export function CTAFooter({ headline, subline, buttonLabel, onClick }: CTAFooterProps) {
  return (
    <section className="gr-cta-footer">
      <h2>{headline}</h2>
      <p>{subline}</p>
      <button type="button" onClick={onClick}>
        {buttonLabel}
      </button>
    </section>
  );
}
