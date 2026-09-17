import { useEffect } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import TaskList from "@tiptap/extension-task-list";
import TaskItem from "@tiptap/extension-task-item";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";

export default function NoteEditor(props: {
  noteId: string | null;
  initialText: string;
  locked: boolean;
  onUnlock: () => void;
  onChange: (text: string) => void;
}) {
  const { noteId, initialText } = props;
  const editor = useEditor(
    {
      extensions: [
        StarterKit.configure({ codeBlock: {} }),
        TaskList,
        TaskItem.configure({ nested: true }),
        Table.configure({ resizable: true }),
        TableRow,
        TableHeader,
        TableCell,
        Placeholder.configure({ placeholder: "Start typing…  #tag supported" }),
      ],
      content: `<p>${initialText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\n/g, "</p><p>")}</p>`,
      editorProps: { attributes: { class: "notty-tiptap" } },
      onUpdate: ({ editor }) => props.onChange(editor.getText()),
    },
    [noteId]
  );

  useEffect(() => {
    if (editor && editor.getText() !== initialText) {
      editor.commands.setContent(
        `<p>${initialText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\n/g, "</p><p>")}</p>`
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [noteId]);

  if (!noteId) {
    return (
      <div className="notty-empty">
        <div className="title">No note selected</div>
        <div className="subtitle">Pick a note or press Ctrl+N</div>
      </div>
    );
  }
  if (props.locked) {
    return (
      <div className="notty-empty">
        <div className="title">🔒 Locked</div>
        <div className="subtitle">Body hidden until unlocked</div>
        <button className="notty-empty-cta" onClick={props.onUnlock}>Unlock</button>
      </div>
    );
  }
  return (
    <div className="notty-editor-card">
      <div className="notty-toolbar">
        <button onClick={() => editor?.chain().focus().toggleBold().run()} title="Bold"><b>B</b></button>
        <button onClick={() => editor?.chain().focus().toggleItalic().run()} title="Italic"><i>I</i></button>
        <button onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()} title="H1">H1</button>
        <button onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()} title="H2">H2</button>
        <button onClick={() => editor?.chain().focus().toggleBulletList().run()} title="Bullets">•</button>
        <button onClick={() => editor?.chain().focus().toggleTaskList().run()} title="Checklist">☑</button>
        <button onClick={() => editor?.chain().focus().toggleCodeBlock().run()} title="Code block">{"</>"}</button>
        <button onClick={() => editor?.chain().focus().toggleBlockquote().run()} title="Quote">”</button>
        <button onClick={() => editor?.chain().focus().insertTable({ rows: 3, cols: 3 }).run()} title="Table (new in Tauri port)">▦</button>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
