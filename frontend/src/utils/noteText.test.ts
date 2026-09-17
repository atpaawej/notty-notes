import { describe, expect, it } from "vitest";
import { buildFtsQuery, extractTitle, makePreview } from "./noteText";

describe("noteText parity with Python core", () => {
  it("extracts first-line title, 80 chars, Untitled fallback", () => {
    expect(extractTitle("My Title\nbody")).toBe("My Title");
    expect(extractTitle("")).toBe("Untitled");
    expect(extractTitle("x".repeat(100))).toBe("x".repeat(80));
  });
  it("builds preview like Db.create_note", () => {
    expect(makePreview("T", "Hello\nWorld")).toBe("Hello World");
    expect(makePreview("T", "")).toBe("T");
    expect(makePreview("", "")).toBe("Untitled");
  });
  it("builds FTS prefix query like Db.list_notes", () => {
    expect(buildFtsQuery("mil eggs")).toBe('"mil"* "eggs"*');
  });
});
