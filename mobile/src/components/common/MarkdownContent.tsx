import React from 'react';
import Markdown from 'react-native-markdown-display';
import { useTheme } from '../../contexts/ThemeContext';
import { StyleSheet } from 'react-native';

interface MarkdownContentProps {
  content: string;
}

const MarkdownContent: React.FC<MarkdownContentProps> = ({ content }) => {
  const { colors, isDark } = useTheme();

  const markdownStyles = StyleSheet.create({
    body: {
      color: colors.text,
      fontSize: 16,
      lineHeight: 24,
    },
    heading1: {
      color: colors.text,
      fontSize: 28,
      fontWeight: 'bold',
      marginTop: 20,
      marginBottom: 12,
    },
    heading2: {
      color: colors.text,
      fontSize: 24,
      fontWeight: 'bold',
      marginTop: 16,
      marginBottom: 10,
    },
    heading3: {
      color: colors.text,
      fontSize: 20,
      fontWeight: 'bold',
      marginTop: 14,
      marginBottom: 8,
    },
    heading4: {
      color: colors.text,
      fontSize: 18,
      fontWeight: '600',
      marginTop: 12,
      marginBottom: 6,
    },
    heading5: {
      color: colors.text,
      fontSize: 16,
      fontWeight: '600',
      marginTop: 10,
      marginBottom: 4,
    },
    heading6: {
      color: colors.text,
      fontSize: 14,
      fontWeight: '600',
      marginTop: 8,
      marginBottom: 4,
    },
    strong: {
      fontWeight: 'bold',
      color: colors.text,
    },
    em: {
      fontStyle: 'italic',
      color: colors.text,
    },
    link: {
      color: colors.primary,
      textDecorationLine: 'underline',
    },
    blockquote: {
      backgroundColor: colors.surface,
      borderLeftWidth: 4,
      borderLeftColor: colors.primary,
      paddingLeft: 12,
      paddingVertical: 8,
      marginVertical: 8,
    },
    code_inline: {
      backgroundColor: colors.surface,
      color: colors.primary,
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 4,
      fontFamily: 'monospace',
      fontSize: 14,
    },
    code_block: {
      backgroundColor: colors.surface,
      color: colors.text,
      padding: 12,
      borderRadius: 8,
      fontFamily: 'monospace',
      fontSize: 14,
      marginVertical: 8,
      borderWidth: 1,
      borderColor: colors.border,
    },
    fence: {
      backgroundColor: colors.surface,
      color: colors.text,
      padding: 12,
      borderRadius: 8,
      fontFamily: 'monospace',
      fontSize: 14,
      marginVertical: 8,
      borderWidth: 1,
      borderColor: colors.border,
    },
    bullet_list: {
      marginVertical: 8,
    },
    ordered_list: {
      marginVertical: 8,
    },
    list_item: {
      flexDirection: 'row',
      marginBottom: 4,
    },
    bullet_list_icon: {
      marginRight: 8,
      color: colors.textSecondary,
    },
    ordered_list_icon: {
      marginRight: 8,
      color: colors.textSecondary,
    },
    paragraph: {
      marginVertical: 4,
      color: colors.text,
    },
    hr: {
      backgroundColor: colors.border,
      height: 1,
      marginVertical: 16,
    },
    table: {
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 8,
      marginVertical: 8,
    },
    thead: {
      backgroundColor: colors.surface,
    },
    tbody: {},
    th: {
      flex: 1,
      padding: 8,
      borderWidth: 1,
      borderColor: colors.border,
      fontWeight: 'bold',
      color: colors.text,
    },
    tr: {
      flexDirection: 'row',
      borderBottomWidth: 1,
      borderColor: colors.border,
    },
    td: {
      flex: 1,
      padding: 8,
      borderWidth: 1,
      borderColor: colors.border,
      color: colors.text,
    },
  });

  return (
    <Markdown style={markdownStyles}>
      {content}
    </Markdown>
  );
};

export default MarkdownContent;
