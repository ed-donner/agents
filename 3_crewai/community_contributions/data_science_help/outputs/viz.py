import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import pandas as pd
import numpy as np

class VizToolKit:
    def visualization(self, cleaned_csv_path: str, task_type: str, target: str = None) -> dict:
        
        # Create output directory if not exists
        output_dir = 'outputs/plots/'
        os.makedirs(output_dir, exist_ok=True)

        # Load cleaned data
        df = pd.read_csv(cleaned_csv_path)
        visual_summary = {}

         # Target distribution (for supervised learning
        if task_type == 'supervised' and target is not None and target in df.columns:
            plt.figure(figsize=(8, 5))
            sns.histplot(df[target], kde=True)
            plt.title('Target Distribution')
            target_dist_path = os.path.join(output_dir, 'target_distribution.png')
            plt.tight_layout()
            plt.savefig(target_dist_path, dpi=150, bbox_inches="tight")
            plt.close()
            visual_summary['target_distribution'] = target_dist_path

        # Missing rates plot
        missing_rate = df.isnull().mean() * 100
        plt.figure(figsize=(10, 6))
        missing_rate.sort_values().plot(kind='barh')
        plt.title('Missing Value Rates')
        missing_rate_path = os.path.join(output_dir, 'missing_rates.png')  # ✅ key/filename align
        plt.tight_layout()
        plt.savefig(missing_rate_path, dpi=150, bbox_inches="tight")
        plt.close()
        visual_summary['missing_rates'] = missing_rate_path

       # Correlation heatmap (numeric-only; only if ≥2 numeric cols)
        num_df = df.select_dtypes(include=[np.number])
        if num_df.shape[1] >= 2:
            plt.figure(figsize=(12, 8))
            corr = num_df.corr(numeric_only=True)
            sns.heatmap(corr, cmap='coolwarm', fmt='.2f', annot=False)
            plt.title('Correlation Heatmap')
            corr_heatmap_path = os.path.join(output_dir, 'correlation_heatmap.png')
            plt.tight_layout()
            plt.savefig(corr_heatmap_path, dpi=150, bbox_inches="tight")
            plt.close()
            visual_summary['correlation_heatmap'] = corr_heatmap_path

        # Numeric features histograms/boxplots
        numeric_features = num_df.columns.tolist()[:12]  
        for feature in numeric_features:
            plt.figure(figsize=(10, 5))
            sns.boxplot(x=df[feature])
            plt.title(f'Boxplot of {feature}')
            num_boxplot_path = os.path.join(output_dir, f'boxplot_{feature}.png')
            plt.tight_layout()
            plt.savefig(num_boxplot_path, dpi=120, bbox_inches="tight")
            plt.close()
            visual_summary[f'boxplot_{feature}'] = num_boxplot_path

            plt.figure(figsize=(10, 5))
            sns.histplot(df[feature], bins=30, kde=True)
            plt.title(f'Histogram of {feature}')
            num_hist_path = os.path.join(output_dir, f'histogram_{feature}.png')
            plt.tight_layout()
            plt.savefig(num_hist_path, dpi=120, bbox_inches="tight")
            plt.close()
            visual_summary[f'histogram_{feature}'] = num_hist_path

        # Categorical feature barplots
        categorical_features = df.select_dtypes(include=['object', 'category']).columns.tolist()[:12]  # ✅ cap to 12
        for feature in categorical_features:
            plt.figure(figsize=(12, 6))
            sns.countplot(data=df, x=feature, order=df[feature].value_counts().index)
            plt.title(f'Barplot of {feature}')
            cat_barplot_path = os.path.join(output_dir, f'barplot_{feature}.png')
            plt.tight_layout()
            plt.savefig(cat_barplot_path, dpi=120, bbox_inches="tight")
            plt.close()
            visual_summary[f'barplot_{feature}'] = cat_barplot_path

        # Write visual summary JSON
        visual_summary_path = 'outputs/visual_summary.json'
        with open(visual_summary_path, 'w', encoding='utf-8') as json_file:  # ✅ safer write
            json.dump(visual_summary, json_file, indent=2, ensure_ascii=False)

        return visual_summary