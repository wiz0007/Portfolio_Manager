import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from './Table';

describe('Table Component', () => {
  it('renders table headers and numeric cells properly', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Asset</TableHead>
            <TableHead numeric align="right">Value</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Bitcoin</TableCell>
            <TableCell numeric align="right">$90,000</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    expect(screen.getByText('Asset')).toBeDefined();
    expect(screen.getByText('$90,000')).toBeDefined();
  });
});

