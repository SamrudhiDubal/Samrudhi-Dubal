import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MatchScoreBadge from '../../components/MatchScoreBadge';

describe('MatchScoreBadge', () => {
  it('renders the percentage text', () => {
    render(<MatchScoreBadge score={82} />);
    expect(screen.getByText('82% AI Match')).toBeInTheDocument();
  });

  it('uses the emerald (strong match) color for high scores', () => {
    render(<MatchScoreBadge score={90} />);
    expect(screen.getByText('90% AI Match')).toHaveClass('bg-emerald-100', 'text-emerald-700');
  });

  it('uses the amber (medium match) color for mid scores', () => {
    render(<MatchScoreBadge score={60} />);
    expect(screen.getByText('60% AI Match')).toHaveClass('bg-amber-100', 'text-amber-700');
  });

  it('uses the rose (weak match) color for low scores', () => {
    render(<MatchScoreBadge score={10} />);
    expect(screen.getByText('10% AI Match')).toHaveClass('bg-rose-100', 'text-rose-700');
  });
});
