import { Extension } from '@tiptap/core';

export interface MarkdownShortcutsOptions {
  // Options for markdown shortcuts
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    markdownShortcuts: {
      /**
       * Convert markdown shortcuts to formatting
       */
      convertMarkdownShortcuts: () => ReturnType;
    };
  }
}

export const MarkdownShortcuts = Extension.create<MarkdownShortcutsOptions>({
  name: 'markdownShortcuts',

  addKeyboardShortcuts() {
    return {
      ' ': ({ editor }) => {
        const { selection } = editor.state;
        const { $from } = selection;
        const currentNode = $from.parent;
        const text = currentNode.textContent;

        // Handle heading shortcuts
        if (text === '#') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 1, to: $from.pos })
            .setHeading({ level: 1 })
            .run();
        }
        
        if (text === '##') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 2, to: $from.pos })
            .setHeading({ level: 2 })
            .run();
        }
        
        if (text === '###') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 3, to: $from.pos })
            .setHeading({ level: 3 })
            .run();
        }

        // Handle list shortcuts
        if (text === '*' || text === '-') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 1, to: $from.pos })
            .toggleBulletList()
            .run();
        }

        if (text === '1.') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 2, to: $from.pos })
            .toggleOrderedList()
            .run();
        }

        // Handle blockquote shortcut
        if (text === '>') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 1, to: $from.pos })
            .toggleBlockquote()
            .run();
        }

        // Handle task list shortcut
        if (text === '[]' || text === '[ ]') {
          return editor.chain()
            .deleteRange({ from: $from.pos - text.length, to: $from.pos })
            .toggleTaskList()
            .run();
        }

        // Handle code block shortcut
        if (text === '```') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 3, to: $from.pos })
            .toggleCodeBlock()
            .run();
        }

        // Handle horizontal rule shortcut
        if (text === '---') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 3, to: $from.pos })
            .setHorizontalRule()
            .run();
        }

        return false;
      },
    };
  },

  addCommands() {
    return {
      convertMarkdownShortcuts:
        () =>
        ({ commands }) => {
          return true;
        },
    };
  },
});

export default MarkdownShortcuts;