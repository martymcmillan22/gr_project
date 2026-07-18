import { useMemo, useState } from "react";
import { buildArtifactTags, formatArtifactTags } from "../logic/artifactTagging";
import { getAvailableCommandPowers, getIdeaGeometryMode } from "../logic/pipelineLogic";
import type { IdeaRecord, ProfileKind, TemporalGroup, Tier } from "../types";

interface IdeaEditorProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  temporalGroup: TemporalGroup;
  tier: Tier;
  phaseColor: string;
  onCreate: (idea: IdeaRecord) => void;
  existingIdea: IdeaRecord | null;
}

export default function IdeaEditor({
  profile,
  compartmentName,
  compartmentIndex,
  temporalGroup,
  tier,
  phaseColor,
  onCreate,
  existingIdea,
}: IdeaEditorProps) {
  const [title, setTitle] = useState(existingIdea?.title || "");
  const [description, setDescription] = useState(existingIdea?.description || "");
  const [tagsInput, setTagsInput] = useState(existingIdea?.tags.join(", ") || "");

  const geometryMode = getIdeaGeometryMode(tier);
  const commands = getAvailableCommandPowers(tier);
  const tagPreview = useMemo(
    () =>
      buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "create",
        temporalGroup,
        tier,
      }),
    [compartmentIndex, compartmentName, profile, temporalGroup, tier],
  );

  const helperText = useMemo(() => {
    if (tier === "novice") {
      return "Novice mode: lightweight idea capture (4 commands).";
    }
    return `Higher-tier mode: ${geometryMode} geometry and expanded commands.`;
  }, [geometryMode, tier]);

  const createIdea = () => {
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      return;
    }
    const cleanTags = tagsInput
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    const idea: IdeaRecord = {
      idea_id: `idea-${Date.now()}`,
      title: cleanTitle,
      description: description.trim(),
      tags: cleanTags,
      temporal_group: temporalGroup,
      phase: "create",
      tier,
      created_at: new Date().toISOString(),
      geometry_mode: geometryMode,
      artifact_tags: buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "create",
        temporalGroup,
        tier,
      }),
    };

    onCreate(idea);
  };

  return (
    <article className="pipeline-card" data-color={phaseColor}>
      <h3>Idea Creation</h3>
      <p>{helperText}</p>
      <p>Command powers: {commands.join(", ")}</p>
      <p>Temporal group: {temporalGroup}</p>
      <p>Artifact tags: {formatArtifactTags(tagPreview)}</p>

      <label>
        Title
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Idea title" />
      </label>

      <label>
        Description
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Describe the idea"
          rows={3}
        />
      </label>

      <label>
        Tags (comma-separated)
        <input value={tagsInput} onChange={(event) => setTagsInput(event.target.value)} placeholder="topic, signal" />
      </label>

      <button type="button" onClick={createIdea}>
        Create Idea
      </button>
    </article>
  );
}
