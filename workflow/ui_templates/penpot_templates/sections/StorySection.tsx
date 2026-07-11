export type StorySectionProps = {
  eyebrow: string;
  title: string;
  body: string;
};

export function StorySection({ eyebrow, title, body }: StorySectionProps) {
  return (
    <section className="gr-story-section">
      <p className="gr-kicker">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}
