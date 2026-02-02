"""
Database schema and migration tools
"""
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class DatabaseSchemaInput(BaseModel):
    """Input schema for database schema generation"""
    database_type: str = Field(..., description="Database type (postgresql, mysql, mongodb)")
    entities: List[Dict[str, Any]] = Field(..., description="Entity definitions")
    include_indexes: bool = Field(default=True, description="Generate index definitions")


class DatabaseSchemaTool(BaseTool):
    name: str = "Database Schema Generator"
    description: str = """
    Generates database schema definitions (SQL DDL or NoSQL schemas).
    Supports PostgreSQL, MySQL, and MongoDB.
    Use this tool to create database structure.
    """
    args_schema: Type[BaseModel] = DatabaseSchemaInput
    
    def _run(
        self,
        database_type: str,
        entities: List[Dict[str, Any]],
        include_indexes: bool = True
    ) -> str:
        """Generate database schema"""
        
        generators = {
            "postgresql": self._generate_postgresql,
            "mysql": self._generate_mysql,
            "mongodb": self._generate_mongodb
        }
        
        generator = generators.get(database_type.lower())
        if not generator:
            return f"❌ Unsupported database type: {database_type}"
        
        return generator(entities, include_indexes)
    
    def _generate_postgresql(self, entities: List[Dict], include_indexes: bool) -> str:
        """Generate PostgreSQL schema"""
        
        sql = "-- PostgreSQL Schema\n\n"
        sql += "-- Enable UUID extension\nCREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n\n"
        
        for entity in entities:
            name = entity.get("name", "entity")
            fields = entity.get("fields", [])
            
            sql += f"-- Table: {name}\n"
            sql += f"CREATE TABLE {name} (\n"
            
            field_lines = []
            for field in fields:
                field_name = field.get("name")
                field_type = self._map_type_postgresql(field.get("type"))
                nullable = "NULL" if field.get("nullable", True) else "NOT NULL"
                default = f"DEFAULT {field.get('default')}" if field.get("default") else ""
                
                if field.get("primary_key"):
                    field_lines.append(f"    {field_name} {field_type} PRIMARY KEY")
                else:
                    field_lines.append(f"    {field_name} {field_type} {nullable} {default}".strip())
            
            # Add audit columns
            field_lines.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
            field_lines.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
            
            sql += ",\n".join(field_lines)
            sql += "\n);\n\n"
            
            # Add indexes
            if include_indexes:
                for field in fields:
                    if field.get("index"):
                        idx_name = f"idx_{name}_{field.get('name')}"
                        sql += f"CREATE INDEX {idx_name} ON {name}({field.get('name')});\n"
                
                sql += "\n"
        
        # Add update trigger function
        sql += """
-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

"""
        
        for entity in entities:
            name = entity.get("name", "entity")
            sql += f"CREATE TRIGGER update_{name}_updated_at\n"
            sql += f"    BEFORE UPDATE ON {name}\n"
            sql += f"    FOR EACH ROW\n"
            sql += f"    EXECUTE FUNCTION update_updated_at_column();\n\n"
        
        return sql
    
    def _generate_mysql(self, entities: List[Dict], include_indexes: bool) -> str:
        """Generate MySQL schema"""
        
        sql = "-- MySQL Schema\n\n"
        
        for entity in entities:
            name = entity.get("name", "entity")
            fields = entity.get("fields", [])
            
            sql += f"-- Table: {name}\n"
            sql += f"CREATE TABLE `{name}` (\n"
            
            field_lines = []
            primary_keys = []
            
            for field in fields:
                field_name = field.get("name")
                field_type = self._map_type_mysql(field.get("type"))
                nullable = "NULL" if field.get("nullable", True) else "NOT NULL"
                default = f"DEFAULT {field.get('default')}" if field.get("default") else ""
                
                if field.get("primary_key"):
                    primary_keys.append(field_name)
                    if field.get("auto_increment"):
                        field_lines.append(f"    `{field_name}` {field_type} NOT NULL AUTO_INCREMENT")
                    else:
                        field_lines.append(f"    `{field_name}` {field_type} NOT NULL")
                else:
                    field_lines.append(f"    `{field_name}` {field_type} {nullable} {default}".strip())
            
            # Add audit columns
            field_lines.append("    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            field_lines.append("    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            
            # Add primary key
            if primary_keys:
                field_lines.append(f"    PRIMARY KEY (`{', '.join(primary_keys)}`)")
            
            sql += ",\n".join(field_lines)
            sql += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        
        return sql
    
    def _generate_mongodb(self, entities: List[Dict], include_indexes: bool) -> str:
        """Generate MongoDB schema validation and indexes"""
        import json
        
        output = "// MongoDB Schema Validation and Indexes\n\n"
        
        for entity in entities:
            name = entity.get("name", "entity")
            fields = entity.get("fields", [])
            
            # Create validation schema
            validation = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": [],
                    "properties": {}
                }
            }
            
            for field in fields:
                field_name = field.get("name")
                bson_type = self._map_type_mongodb(field.get("type"))
                
                validation["$jsonSchema"]["properties"][field_name] = {
                    "bsonType": bson_type,
                    "description": field.get("description", f"The {field_name} field")
                }
                
                if not field.get("nullable", True):
                    validation["$jsonSchema"]["required"].append(field_name)
            
            # Add timestamps
            validation["$jsonSchema"]["properties"]["createdAt"] = {"bsonType": "date"}
            validation["$jsonSchema"]["properties"]["updatedAt"] = {"bsonType": "date"}
            
            output += f"// Collection: {name}\n"
            output += f"db.createCollection('{name}', {{\n"
            output += f"  validator: {json.dumps(validation, indent=4)}\n"
            output += "});\n\n"
            
            # Add indexes
            if include_indexes:
                for field in fields:
                    if field.get("index"):
                        output += f"db.{name}.createIndex({{ {field.get('name')}: 1 }});\n"
                    if field.get("unique"):
                        output += f"db.{name}.createIndex({{ {field.get('name')}: 1 }}, {{ unique: true }});\n"
                
                output += "\n"
        
        return output
    
    def _map_type_postgresql(self, field_type: str) -> str:
        """Map field type to PostgreSQL type"""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "float": "DECIMAL(10,2)",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP WITH TIME ZONE",
            "uuid": "UUID DEFAULT uuid_generate_v4()",
            "json": "JSONB"
        }
        return type_map.get(field_type.lower(), "VARCHAR(255)")
    
    def _map_type_mysql(self, field_type: str) -> str:
        """Map field type to MySQL type"""
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INT",
            "bigint": "BIGINT",
            "float": "DECIMAL(10,2)",
            "boolean": "TINYINT(1)",
            "date": "DATE",
            "datetime": "DATETIME",
            "uuid": "CHAR(36)",
            "json": "JSON"
        }
        return type_map.get(field_type.lower(), "VARCHAR(255)")
    
    def _map_type_mongodb(self, field_type: str) -> str:
        """Map field type to MongoDB BSON type"""
        type_map = {
            "string": "string",
            "text": "string",
            "integer": "int",
            "bigint": "long",
            "float": "double",
            "boolean": "bool",
            "date": "date",
            "datetime": "date",
            "uuid": "string",
            "json": "object"
        }
        return type_map.get(field_type.lower(), "string")


class MigrationInput(BaseModel):
    """Input schema for migration generation"""
    database_type: str = Field(..., description="Database type")
    migration_name: str = Field(..., description="Migration name")
    operations: List[Dict[str, Any]] = Field(..., description="Migration operations")


class MigrationTool(BaseTool):
    name: str = "Migration Generator"
    description: str = """
    Generates database migration scripts.
    Supports Alembic (Python), Flyway, and raw SQL migrations.
    Use this tool to create version-controlled database changes.
    """
    args_schema: Type[BaseModel] = MigrationInput
    
    def _run(
        self,
        database_type: str,
        migration_name: str,
        operations: List[Dict[str, Any]]
    ) -> str:
        """Generate migration script"""
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        migration = f"""\"\"\"
{migration_name}

Revision ID: {timestamp}
Create Date: {datetime.now().isoformat()}
\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
"""
        
        for operation in operations:
            op_type = operation.get("type")
            if op_type == "create_table":
                migration += self._generate_create_table(operation)
            elif op_type == "add_column":
                migration += self._generate_add_column(operation)
            elif op_type == "drop_table":
                migration += self._generate_drop_table(operation)
        
        migration += """

def downgrade():
    pass  # TODO: Implement downgrade
"""
        
        return migration
    
    def _generate_create_table(self, operation: Dict) -> str:
        """Generate create table operation"""
        table_name = operation.get("table")
        columns = operation.get("columns", [])
        
        code = f"    op.create_table('{table_name}',\n"
        
        for col in columns:
            col_type = col.get("type", "String")
            code += f"        sa.Column('{col.get('name')}', sa.{col_type}()"
            if col.get("primary_key"):
                code += ", primary_key=True"
            if col.get("nullable") is False:
                code += ", nullable=False"
            code += "),\n"
        
        code += "    )\n"
        return code
    
    def _generate_add_column(self, operation: Dict) -> str:
        """Generate add column operation"""
        table_name = operation.get("table")
        column = operation.get("column", {})
        col_type = column.get("type", "String")
        
        return f"    op.add_column('{table_name}', sa.Column('{column.get('name')}', sa.{col_type}()))\n"
    
    def _generate_drop_table(self, operation: Dict) -> str:
        """Generate drop table operation"""
        return f"    op.drop_table('{operation.get('table')}')\n"
