%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffcc00', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#f4f4f4'}}}%%
graph LR
    subgraph External [External Source]
        A[Gmail Server<br/>(IMAP)]:::external
    end

    subgraph Local_Environment [Your Local Laptop / Docker]
        direction TB
        
        subgraph Orchestration [Ingestion & Intelligence Layer]
            B(Python Controller Script):::python
            C[Local Ollama Server<br/>Llama 3 Model]:::ai
        end

        subgraph Storage [Data Warehouse Layer]
            D[(DuckDB Database<br/>'expenses.db')]:::db
        end

        subgraph Transformation [Semantic Layer]
            E{dbt-core}:::dbt
        end

        subgraph Serving [Presentation Layer]
            F(Streamlit Dashboard<br/>localhost:8501)::viz
        end
    end

    %% Data Flow Connections
    B -->|1. Fetch Emails (SSL)| A
    B -->|2. Send Raw Text| C
    C -- "3. Return Structured Data (JSON)" --> B
    B -->|4. Load Raw Records| D
    E -->|5. Transform & Test Models| D
    F -->|6. Query Analytics Views| D

    %% Styling classes
    classDef external fill:#e1e1e1,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5;
    classDef python fill:#3776ab,stroke:#fff,color:#fff,stroke-width:2px;
    classDef ai fill:#ff6600,stroke:#fff,color:#fff,stroke-width:2px;
    classDef db fill:#fff200,stroke:#333,stroke-width:2px;
    classDef dbt fill:#FF6B55,stroke:#fff,color:#fff,stroke-width:2px;
    classDef viz fill:#ff4b4b,stroke:#fff,color:#fff,stroke-width:2px;