import os
import json
from typing import Any, List, cast, Optional, Literal, Dict


from llama_index.vector_stores.docarray.base import DocArrayVectorStore

class DocArrayHnswVectorStore(DocArrayVectorStore):
    def __init__(
        self,
        work_dir: str,
        dim: int = 1536,
        dist_metric: Literal["cosine", "ip", "l2"] = "cosine",
        max_elements: int = 1024,
        ef_construction: int = 200,
        ef: int = 10,
        M: int = 16,
        allow_replace_deleted: bool = True,
        num_threads: int = 1,
    ):
        import_err_msg = """
                `docarray` package not found. Install the package via pip:
                `pip install docarray[hnswlib]`
        """
        try:
            import docarray  # noqa: F401
        except ImportError:
            raise ImportError(import_err_msg)

        self._work_dir = work_dir
        ref_docs_path = os.path.join(self._work_dir, 'ref_docs.json')
        if os.path.exists(ref_docs_path):
            with open(ref_docs_path, 'r') as f:
                self._ref_docs = json.load(f)
        else:
            self._ref_docs = {}

        self._index, self._schema = self._init_index(
            dim=dim,
            dist_metric=dist_metric,
            max_elements=max_elements,
            ef_construction=ef_construction,
            ef=ef,
            M=M,
            allow_replace_deleted=allow_replace_deleted,
            num_threads=num_threads,
        )

    def _init_index(self, **kwargs):
        from docarray.index import HnswDocumentIndex

        schema = self._get_schema(**kwargs)
        return HnswDocumentIndex[schema](work_dir=self._work_dir), schema

    def _find_docs_to_be_removed(self, doc_id):
        docs = self._ref_docs.get(doc_id)
        del self._ref_docs[doc_id]
        self._save_ref_docs()
        return docs

    def _save_ref_docs(self):
        with open(os.path.join(self._work_dir, 'ref_docs.json') , 'w') as f:
            json.dump(self._ref_docs, f)

    def _update_ref_docs(self, docs):
        for doc in docs:
            if doc.metadata['doc_id'] not in self._ref_docs:
                self._ref_docs[doc.metadata['doc_id']] = []
            self._ref_docs[doc.metadata['doc_id']].append(doc.id)
        self._save_ref_docs()