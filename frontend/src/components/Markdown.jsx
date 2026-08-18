/**
 * Minimal, dependency-free Markdown renderer for LLM answers.
 *
 * Supports the subset the model actually emits: fenced code blocks, headings,
 * unordered/ordered lists, **bold**, and `inline code`. Renders to React nodes
 * (no HTML injection), so there's no XSS surface from model output.
 */

// Inline formatting within a line: `code` and **bold**.
function renderInline(text) {
  const nodes = [];
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) nodes.push(text.slice(lastIndex, match.index));

    const token = match[0];
    if (token.startsWith("`")) {
      nodes.push(
        <code
          key={key++}
          className="rounded border border-slate-200 bg-slate-100 px-1.5 py-0.5 font-mono text-[0.85em] text-rose-600"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else {
      nodes.push(
        <strong key={key++} className="font-semibold text-slate-900">
          {token.slice(2, -2)}
        </strong>
      );
    }
    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) nodes.push(text.slice(lastIndex));
  return nodes;
}

const isFence = (l) => l.trimStart().startsWith("```");
const isUl = (l) => /^\s*[*-]\s+/.test(l);
const isOl = (l) => /^\s*\d+\.\s+/.test(l);
const isHeading = (l) => /^#{1,6}\s+/.test(l);

export default function Markdown({ text }) {
  const lines = (text || "").split("\n");
  const blocks = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block.
    if (isFence(line)) {
      const code = [];
      i++;
      while (i < lines.length && !isFence(lines[i])) code.push(lines[i++]);
      i++; // skip closing fence
      blocks.push(
        <div
          key={key++}
          className="my-3 overflow-hidden rounded-md border border-slate-700"
        >
          {/* Title bar so a multi-line block reads clearly as code. */}
          <div className="flex items-center gap-1.5 border-b border-slate-700 bg-slate-800 px-3 py-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-green-400/70" />
            <span className="ml-2 font-mono text-[0.7rem] uppercase tracking-wide text-slate-400">
              code
            </span>
          </div>
          <pre className="overflow-x-auto bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">
            <code className="font-mono">{code.join("\n")}</code>
          </pre>
        </div>
      );
      continue;
    }

    // Blank line.
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Heading.
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length;
      const size = level === 1 ? "text-base" : "text-sm";
      blocks.push(
        <p key={key++} className={`mb-1 mt-3 font-semibold text-slate-900 ${size}`}>
          {renderInline(heading[2])}
        </p>
      );
      i++;
      continue;
    }

    // Unordered list.
    if (isUl(line)) {
      const items = [];
      while (i < lines.length && isUl(lines[i])) {
        items.push(lines[i].replace(/^\s*[*-]\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={key++} className="my-2 list-disc space-y-1 pl-5">
          {items.map((it, idx) => (
            <li key={idx}>{renderInline(it)}</li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered list.
    if (isOl(line)) {
      const items = [];
      while (i < lines.length && isOl(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      blocks.push(
        <ol key={key++} className="my-2 list-decimal space-y-1 pl-5">
          {items.map((it, idx) => (
            <li key={idx}>{renderInline(it)}</li>
          ))}
        </ol>
      );
      continue;
    }

    // Paragraph: gather consecutive plain lines.
    const para = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !isFence(lines[i]) &&
      !isUl(lines[i]) &&
      !isOl(lines[i]) &&
      !isHeading(lines[i])
    ) {
      para.push(lines[i]);
      i++;
    }
    blocks.push(
      <p key={key++} className="my-2 leading-relaxed">
        {renderInline(para.join(" "))}
      </p>
    );
  }

  return <div className="text-sm text-slate-800">{blocks}</div>;
}
