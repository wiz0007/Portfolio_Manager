import { forwardRef } from 'react';
import {
  TableProps,
  TableHeaderProps,
  TableBodyProps,
  TableRowProps,
  TableHeadProps,
  TableCellProps,
} from './Table.types';
import styles from './Table.module.css';

export const Table = forwardRef<HTMLTableElement, TableProps>(
  ({ density = 'comfortable', className = '', children, ...props }, ref) => {
    const densityClass = density === 'compact' ? styles.compact : styles.comfortable;
    return (
      <div className={styles.wrapper}>
        <table ref={ref} className={`${styles.table} ${densityClass} ${className}`.trim()} {...props}>
          {children}
        </table>
      </div>
    );
  }
);
Table.displayName = 'Table';

export const TableHeader = forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ className = '', children, ...props }, ref) => (
    <thead ref={ref} className={`${styles.header} ${className}`.trim()} {...props}>
      {children}
    </thead>
  )
);
TableHeader.displayName = 'TableHeader';

export const TableBody = forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ className = '', children, ...props }, ref) => (
    <tbody ref={ref} className={className} {...props}>
      {children}
    </tbody>
  )
);
TableBody.displayName = 'TableBody';

export const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ isClickable = false, className = '', children, ...props }, ref) => (
    <tr
      ref={ref}
      className={`${styles.row} ${isClickable ? styles.clickableRow : ''} ${className}`.trim()}
      {...props}
    >
      {children}
    </tr>
  )
);
TableRow.displayName = 'TableRow';

export const TableHead = forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ align = 'left', numeric = false, className = '', children, ...props }, ref) => {
    const alignClass = {
      left: styles.alignLeft,
      center: styles.alignCenter,
      right: styles.alignRight,
    }[align];

    const classNames = [
      styles.head,
      alignClass,
      numeric ? styles.numeric : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <th ref={ref} className={classNames} {...props}>
        {children}
      </th>
    );
  }
);
TableHead.displayName = 'TableHead';

export const TableCell = forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ align = 'left', numeric = false, className = '', children, ...props }, ref) => {
    const alignClass = {
      left: styles.alignLeft,
      center: styles.alignCenter,
      right: styles.alignRight,
    }[align];

    const classNames = [
      styles.cell,
      alignClass,
      numeric ? styles.numeric : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <td ref={ref} className={classNames} {...props}>
        {children}
      </td>
    );
  }
);
TableCell.displayName = 'TableCell';
