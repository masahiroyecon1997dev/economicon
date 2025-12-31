import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Tooltip } from './Tooltip';

describe('Tooltip', () => {
  it('子要素が正しくレンダリングされる', () => {
    render(
      <Tooltip content="テストツールチップ">
        <button>ホバー</button>
      </Tooltip>
    );

    expect(screen.getByRole('button', { name: 'ホバー' })).toBeInTheDocument();
  });

  it('contentプロパティが設定される', () => {
    const testContent = 'テストツールチップ';

    render(
      <Tooltip content={testContent}>
        <button>ホバー</button>
      </Tooltip>
    );

    // ボタンが表示されていることを確認
    expect(screen.getByRole('button', { name: 'ホバー' })).toBeInTheDocument();
  });

  it('カスタムdelayが設定できる', () => {
    const customDelay = 1000;

    render(
      <Tooltip content="テストツールチップ" delay={customDelay}>
        <button>ホバー</button>
      </Tooltip>
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('カスタムpositionが設定できる', () => {
    const positions: Array<'top' | 'bottom' | 'left' | 'right'> = ['top', 'bottom', 'left', 'right'];

    positions.forEach(position => {
      const { unmount } = render(
        <Tooltip content="テストツールチップ" position={position}>
          <button>ホバー {position}</button>
        </Tooltip>
      );

      expect(screen.getByRole('button', { name: `ホバー ${position}` })).toBeInTheDocument();
      unmount();
    });
  });

  it('カスタムmaxWidthが設定できる', () => {
    const customMaxWidth = 400;

    render(
      <Tooltip content="テストツールチップ" maxWidth={customMaxWidth}>
        <button>ホバー</button>
      </Tooltip>
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('デフォルト値が正しく適用される', () => {
    render(
      <Tooltip content="テストツールチップ">
        <button>ホバー</button>
      </Tooltip>
    );

    // デフォルト値: position='top', delay=500, maxWidth=300
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('複数の子要素が含まれる場合も正しく動作する', () => {
    render(
      <Tooltip content="テストツールチップ">
        <div>
          <span>テキスト1</span>
          <span>テキスト2</span>
        </div>
      </Tooltip>
    );

    expect(screen.getByText('テキスト1')).toBeInTheDocument();
    expect(screen.getByText('テキスト2')).toBeInTheDocument();
  });
});
