import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { Reel } from "./Reel";
import { Studio } from "./studio/Studio";
import type { StudioProps } from "./studio/types";
import { demoProps } from "./demo";
import type { ReelProps } from "./types";

const calc: CalculateMetadataFunction<ReelProps> = async ({ props }) => ({
  durationInFrames: Math.max(1, Math.ceil(props.durationSec * props.fps)),
  fps: props.fps,
  defaultOutName: props.meta.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 60),
});

const calcStudio: CalculateMetadataFunction<StudioProps> = async ({ props }) => ({
  durationInFrames: Math.max(1, Math.ceil(props.durationSec * props.fps)),
  fps: props.fps,
});

const studioDemo: StudioProps = {
  meta: { title: "demo", look: "studio" }, durationSec: 3, fps: 30, audio: { sfx: [] }, words: [], emphasis: [],
  layouts: [{ t: 0, layout: "off" }], shots: [{ id: "a", from: 0, to: 3, kind: "scene", type: "title", props: { lines: ["Studio"] } }], gfx: [],
};

export const RemotionRoot: React.FC = () => (
  <>
  <Composition
    id="Studio"
    component={Studio as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={90}
    defaultProps={studioDemo as unknown as Record<string, unknown>}
    calculateMetadata={calcStudio as unknown as CalculateMetadataFunction<Record<string, unknown>>}
  />
  <Composition
    id="Reel"
    component={Reel as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={300}
    defaultProps={demoProps as unknown as Record<string, unknown>}
    calculateMetadata={calc as unknown as CalculateMetadataFunction<Record<string, unknown>>}
  />
  </>
);
