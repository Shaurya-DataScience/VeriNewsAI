import os
import sys
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from training.dataset_preprocessor import load_and_preprocess_datasets, NUMERIC_LABEL_MAP, REVERSE_NUMERIC_LABEL_MAP

MODEL_SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "distilbert_factchecker")

class ClaimDataset(Dataset):
    def __init__(self, texts, labels, tokenizer=None, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        if self.tokenizer is not None:
            encoding = self.tokenizer(
                text,
                truncation=True,
                padding="max_length",
                max_length=self.max_length,
                return_tensors="pt"
            )
            item = {key: val.squeeze(0) for key, val in encoding.items()}
            item["labels"] = torch.tensor(label, dtype=torch.long)
            return item
        else:
            return {"text": text, "labels": torch.tensor(label, dtype=torch.long)}

def train_model(max_samples=None, epochs=2, batch_size=16, lr=2e-5):
    """
    Train DistilBERT claim classifier for fact verification.
    """
    print("[Trainer] Starting DistilBERT Claim Classification Training...")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    texts, labels = load_and_preprocess_datasets(data_dir)

    if max_samples and max_samples < len(texts):
        print(f"[Trainer] Subsampling dataset to max {max_samples} samples...")
        idx = np.random.choice(len(texts), max_samples, replace=False)
        texts = [texts[i] for i in idx]
        labels = [labels[i] for i in idx]

    # Leak-free Train (70%), Validation (15%), Test (15%) split with safe stratification
    from collections import Counter
    def get_stratify(y):
        counts = Counter(y)
        if len(counts) > 1 and all(c >= 2 for c in counts.values()):
            return y
        return None

    train_texts, test_val_texts, train_labels, test_val_labels = train_test_split(
        texts, labels, test_size=0.30, random_state=42, stratify=get_stratify(labels)
    )
    val_texts, test_texts, val_labels, test_labels = train_test_split(
        test_val_texts, test_val_labels, test_size=0.50, random_state=42, stratify=get_stratify(test_val_labels)
    )

    print(f"[Trainer] Data Splits -> Train: {len(train_texts)}, Validation: {len(val_texts)}, Test: {len(test_texts)}")

    # Calculate class weights for cross entropy loss balancing
    try:
        from sklearn.utils.class_weight import compute_class_weight
        unique_classes = np.unique(train_labels)
        weights = compute_class_weight(class_weight="balanced", classes=unique_classes, y=train_labels)
        class_weights_dict = {cls: w for cls, w in zip(unique_classes, weights)}
        print(f"[Trainer] Class Weights for Loss Balancing: {class_weights_dict}")
    except Exception as e:
        print(f"[Trainer] Notice: class_weight calculation notice: {e}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Trainer] Using device: {device}")

    has_transformers = False
    try:
        from transformers import DistilBertTokenizerFast, AutoModelForSequenceClassification, AdamW
        has_transformers = True
    except ImportError:
        print("[Trainer] Transformers library not found. Installing or using embedding classifier fallback...")

    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)

    if has_transformers:
        try:
            tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
            model = AutoModelForSequenceClassification.from_pretrained(
                "distilbert-base-uncased",
                num_labels=4
            ).to(device)

            train_dataset = ClaimDataset(train_texts, train_labels, tokenizer=tokenizer)
            val_dataset = ClaimDataset(val_texts, val_labels, tokenizer=tokenizer)

            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

            optimizer = AdamW(model.parameters(), lr=lr)

            best_val_loss = float("inf")
            patience = 3
            patience_counter = 0

            for epoch in range(epochs):
                model.train()
                total_train_loss = 0
                for batch in train_loader:
                    optimizer.zero_grad()
                    input_ids = batch["input_ids"].to(device)
                    attention_mask = batch["attention_mask"].to(device)
                    b_labels = batch["labels"].to(device)

                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=b_labels)
                    loss = outputs.loss
                    loss.backward()
                    optimizer.step()
                    total_train_loss += loss.item()

                avg_train_loss = total_train_loss / len(train_loader)

                # Validation Loop
                model.eval()
                val_preds = []
                val_true = []
                total_val_loss = 0
                with torch.no_grad():
                    for batch in val_loader:
                        input_ids = batch["input_ids"].to(device)
                        attention_mask = batch["attention_mask"].to(device)
                        b_labels = batch["labels"].to(device)

                        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=b_labels)
                        total_val_loss += outputs.loss.item()

                        logits = outputs.logits
                        preds = torch.argmax(logits, dim=1).cpu().numpy()
                        val_preds.extend(preds)
                        val_true.extend(b_labels.cpu().numpy())

                avg_val_loss = total_val_loss / len(val_loader)
                val_acc = accuracy_score(val_true, val_preds)

                print(f"[Epoch {epoch+1}/{epochs}] Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc*100:.2f}%")

                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    print(f"  + Saving best model checkpoint to {MODEL_SAVE_DIR}...")
                    model.save_pretrained(MODEL_SAVE_DIR)
                    tokenizer.save_pretrained(MODEL_SAVE_DIR)
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print("  ! Early stopping triggered.")
                        break

            print("[Trainer] Model training completed successfully!")
            return
        except Exception as e:
            print(f"[Trainer] DistilBERT training exception: {e}. Generating feature embedding classifier checkpoint...")

    # Fallback Lightweight Linear Classifier Checkpoint
    from sentence_transformers import SentenceTransformer
    print("[Trainer] Training SentenceTransformer centroid classifier fallback...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    X_train = embedder.encode(train_texts, show_progress_bar=False)
    X_val = embedder.encode(val_texts, show_progress_bar=False)

    from sklearn.linear_model import LogisticRegression
    import joblib

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, train_labels)
    preds = clf.predict(X_val)
    acc = accuracy_score(val_labels, preds)
    print(f"[Trainer] Fallback Classifier Val Accuracy: {acc*100:.2f}%")

    checkpoint_file = os.path.join(MODEL_SAVE_DIR, "classifier_fallback.joblib")
    joblib.dump(clf, checkpoint_file)
    print(f"[Trainer] Saved fallback checkpoint to {checkpoint_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DistilBERT Claim Classifier for VeriNews AI")
    parser.add_argument("--epochs", type=int, default=2, help="Number of epochs to train")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for training")
    parser.add_argument("--max_samples", type=int, default=500, help="Max samples to train on for fast execution")
    args = parser.parse_args()

    train_model(max_samples=args.max_samples, epochs=args.epochs, batch_size=args.batch_size)
