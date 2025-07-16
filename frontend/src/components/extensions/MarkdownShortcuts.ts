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

        // Handle list shortcuts - improved
        if (text === '*' || text === '-') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 1, to: $from.pos })
            .toggleBulletList()
            .run();
        }

        // Handle numbered list - improved regex pattern
        if (text.match(/^\d+\.$/)) {
          return editor.chain()
            .deleteRange({ from: $from.pos - text.length, to: $from.pos })
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

        // Handle task list shortcut - improved
        if (text === '[]' || text === '[ ]' || text === '[x]') {
          return editor.chain()
            .deleteRange({ from: $from.pos - text.length, to: $from.pos })
            .toggleTaskList()
            .run();
        }

        // Handle code block shortcut - improved
        if (text === '```') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 3, to: $from.pos })
            .toggleCodeBlock()
            .run();
        }

        // Handle horizontal rule shortcut
        if (text === '---' || text === '___') {
          return editor.chain()
            .deleteRange({ from: $from.pos - 3, to: $from.pos })
            .setHorizontalRule()
            .run();
        }

        return false;
      },
      
      // Add inline code shortcut
      '`': ({ editor }) => {
        const { selection } = editor.state;
        const { $from } = selection;
        const currentNode = $from.parent;
        const text = currentNode.textContent;

        // Handle inline code with backticks
        if (text.endsWith('`')) {
          const beforeCursor = text.slice(0, $from.pos - $from.start());
          const lastBacktick = beforeCursor.lastIndexOf('`', beforeCursor.length - 2);
          
          if (lastBacktick !== -1) {
            const codeText = beforeCursor.slice(lastBacktick + 1, beforeCursor.length - 1);
            if (codeText.trim()) {
              return editor.chain()
                .deleteRange({ 
                  from: $from.start() + lastBacktick, 
                  to: $from.pos 
                })
                .insertContent(`<code>${codeText}</code>`)
                .run();
            }
          }
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