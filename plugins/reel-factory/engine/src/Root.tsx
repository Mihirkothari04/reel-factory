import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { Reel } from "./Reel";
import { demoProps } from "./demo";
import type { ReelProps } from "./types";

const calc: CalculateMetadataFunction<ReelProps> = async ({ props }) => ({
  durationInFrames: Math.max(1, Math.ceil(props.durationSec * props.fps)),
  fps: props.fps,
  defaultOutName: props.meta.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 60),
});

export const RemotionRoot: React.FC = () => (
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
);
