export interface Folder {
  id: string;
  name: string;
  created_at: number;
}

export interface Note {
  id: string;
  folder_id: string | null;
  title: string;
  body: string;
  preview: string;
  pinned: boolean;
  locked: boolean;
  created_at: number;
  updated_at: number;
}

export interface TagCount {
  tag: string;
  count: number;
}

export interface ListNotesArgs {
  folder_id?: string;
  query?: string;
  tag?: string | null;
  pinned_only?: boolean;
}
