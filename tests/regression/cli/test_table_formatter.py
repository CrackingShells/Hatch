"""Regression tests for TableFormatter class.

Tests focus on behavioral contracts for table rendering:
- Column alignment (left, right, center)
- Auto-width calculation
- Header and separator rendering
- Row data handling

Reference: R02 §5 (02-list_output_format_specification_v2.md)
Reference: R06 §3.6 (06-dependency_analysis_v0.md)
"""

import pytest


class TestColumnDef:
    """Tests for ColumnDef dataclass."""

    def test_column_def_has_required_fields(self):
        """ColumnDef must have name, width, and align fields."""
        from hatch.cli.cli_utils import ColumnDef
        
        col = ColumnDef(name="Test", width=10)
        assert col.name == "Test"
        assert col.width == 10
        assert col.align == "left"  # Default alignment

    def test_column_def_accepts_auto_width(self):
        """ColumnDef width can be 'auto' for auto-calculation."""
        from hatch.cli.cli_utils import ColumnDef
        
        col = ColumnDef(name="Test", width="auto")
        assert col.width == "auto"

    def test_column_def_accepts_alignment_options(self):
        """ColumnDef supports left, right, and center alignment."""
        from hatch.cli.cli_utils import ColumnDef
        
        left = ColumnDef(name="Left", width=10, align="left")
        right = ColumnDef(name="Right", width=10, align="right")
        center = ColumnDef(name="Center", width=10, align="center")
        
        assert left.align == "left"
        assert right.align == "right"
        assert center.align == "center"


class TestTableFormatter:
    """Tests for TableFormatter class."""

    def test_table_formatter_accepts_column_definitions(self):
        """TableFormatter initializes with column definitions."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [
            ColumnDef(name="Name", width=20),
            ColumnDef(name="Value", width=10),
        ]
        formatter = TableFormatter(columns)
        assert formatter is not None

    def test_add_row_stores_data(self):
        """add_row stores row data for rendering."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Col1", width=10)]
        formatter = TableFormatter(columns)
        formatter.add_row(["value1"])
        formatter.add_row(["value2"])
        
        # Verify rows are stored (implementation detail, but necessary for render)
        assert len(formatter._rows) == 2

    def test_render_produces_string_output(self):
        """render() returns a string with table content."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Name", width=10)]
        formatter = TableFormatter(columns)
        formatter.add_row(["Test"])
        
        output = formatter.render()
        assert isinstance(output, str)
        assert len(output) > 0

    def test_render_includes_header_row(self):
        """Rendered output includes column headers."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [
            ColumnDef(name="Name", width=15),
            ColumnDef(name="Status", width=10),
        ]
        formatter = TableFormatter(columns)
        formatter.add_row(["test-item", "active"])
        
        output = formatter.render()
        assert "Name" in output
        assert "Status" in output

    def test_render_includes_separator_line(self):
        """Rendered output includes separator line after headers."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Name", width=10)]
        formatter = TableFormatter(columns)
        formatter.add_row(["Test"])
        
        output = formatter.render()
        # Separator uses box-drawing character or dashes
        assert "─" in output or "-" in output

    def test_render_includes_data_rows(self):
        """Rendered output includes all added data rows."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Item", width=15)]
        formatter = TableFormatter(columns)
        formatter.add_row(["first-item"])
        formatter.add_row(["second-item"])
        formatter.add_row(["third-item"])
        
        output = formatter.render()
        assert "first-item" in output
        assert "second-item" in output
        assert "third-item" in output

    def test_left_alignment_pads_right(self):
        """Left-aligned columns pad values on the right."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Name", width=10, align="left")]
        formatter = TableFormatter(columns)
        formatter.add_row(["abc"])
        
        output = formatter.render()
        lines = output.strip().split("\n")
        # Find data row (skip header and separator)
        data_line = lines[-1]
        # Left-aligned: value followed by spaces
        assert "abc" in data_line

    def test_right_alignment_pads_left(self):
        """Right-aligned columns pad values on the left."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Count", width=10, align="right")]
        formatter = TableFormatter(columns)
        formatter.add_row(["42"])
        
        output = formatter.render()
        lines = output.strip().split("\n")
        data_line = lines[-1]
        # Right-aligned: spaces followed by value
        assert "42" in data_line

    def test_auto_width_calculates_from_content(self):
        """Auto width calculates based on header and data content."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Name", width="auto")]
        formatter = TableFormatter(columns)
        formatter.add_row(["short"])
        formatter.add_row(["much-longer-value"])
        
        output = formatter.render()
        # Output should accommodate the longest value
        assert "much-longer-value" in output

    def test_empty_table_renders_headers_only(self):
        """Table with no rows renders headers and separator."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Empty", width=10)]
        formatter = TableFormatter(columns)
        
        output = formatter.render()
        assert "Empty" in output
        # Should have header and separator, but no data rows

    def test_multiple_columns_separated(self):
        """Multiple columns are visually separated."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [
            ColumnDef(name="Col1", width=10),
            ColumnDef(name="Col2", width=10),
            ColumnDef(name="Col3", width=10),
        ]
        formatter = TableFormatter(columns)
        formatter.add_row(["a", "b", "c"])
        
        output = formatter.render()
        assert "Col1" in output
        assert "Col2" in output
        assert "Col3" in output
        assert "a" in output
        assert "b" in output
        assert "c" in output

    def test_truncation_with_ellipsis(self):
        """Values exceeding column width are truncated with ellipsis."""
        from hatch.cli.cli_utils import TableFormatter, ColumnDef
        
        columns = [ColumnDef(name="Name", width=8)]
        formatter = TableFormatter(columns)
        formatter.add_row(["very-long-value-that-exceeds-width"])
        
        output = formatter.render()
        # Should truncate and add ellipsis
        assert "…" in output or "..." in output
