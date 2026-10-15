import { describe, it, expect } from "vitest";
import {
  formatOdds,
  formatProbability,
  hasValue,
  formatEdge,
  parseForm,
  matchResult,
} from "../utils";

describe("formatOdds", () => {
  it("formats decimal odds", () => {
    expect(formatOdds(2.5, "decimal")).toBe("2.50");
    expect(formatOdds(1.8, "decimal")).toBe("1.80");
  });

  it("formats american odds for favorites", () => {
    expect(formatOdds(1.5, "american")).toBe("-200");
  });

  it("formats american odds for underdogs", () => {
    expect(formatOdds(3.0, "american")).toBe("+200");
  });

  it("formats fractional odds", () => {
    expect(formatOdds(2.0, "fractional")).toBe("1/1");
    expect(formatOdds(3.0, "fractional")).toBe("2/1");
  });
});

describe("formatProbability", () => {
  it("formats as percentage", () => {
    expect(formatProbability(0.55)).toBe("55%");
    expect(formatProbability(0.333)).toBe("33%");
  });

  it("formats with decimals", () => {
    expect(formatProbability(0.555, 1)).toBe("55.5%");
  });
});

describe("hasValue", () => {
  it("returns true when edge >= 3pp and confidence is medium or high", () => {
    expect(hasValue(0.55, 0.50, "medium")).toBe(true);
    expect(hasValue(0.60, 0.50, "high")).toBe(true);
  });

  it("returns false when edge < 3pp", () => {
    expect(hasValue(0.52, 0.50, "high")).toBe(false);
  });

  it("returns false when confidence is low", () => {
    expect(hasValue(0.60, 0.50, "low")).toBe(false);
  });
});

describe("formatEdge", () => {
  it("formats positive edge with + sign", () => {
    expect(formatEdge(0.05)).toBe("+5.0pp");
  });

  it("formats negative edge", () => {
    expect(formatEdge(-0.03)).toBe("-3.0pp");
  });
});

describe("parseForm", () => {
  it("parses form string into array", () => {
    expect(parseForm("WWDLL")).toEqual(["W", "W", "D", "L", "L"]);
  });

  it("filters invalid characters", () => {
    expect(parseForm("W-D-L")).toEqual(["W", "D", "L"]);
  });
});

describe("matchResult", () => {
  it("returns W for home team win when team is home", () => {
    expect(matchResult(2, 1, "team-a", "team-a")).toBe("W");
  });

  it("returns L for home team win when team is away", () => {
    expect(matchResult(2, 1, "team-b", "team-a")).toBe("L");
  });

  it("returns D for draw", () => {
    expect(matchResult(1, 1, "team-a", "team-a")).toBe("D");
  });
});