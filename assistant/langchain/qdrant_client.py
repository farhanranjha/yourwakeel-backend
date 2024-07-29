import hashlib
from itertools import islice
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union
)
import uuid

from langchain_community.vectorstores.qdrant import Qdrant, QdrantException
from langchain_core.embeddings import Embeddings


from qdrant_client.conversions import common_types
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Filter, FieldCondition, FilterSelector, MatchValue

DictFilter = Dict[str, Union[str, int, bool, dict, list]]
MetadataFilter = Union[DictFilter, common_types.Filter]


class CustomQdrantClient(Qdrant):

    CONTENT_KEY = "page_content"
    METADATA_KEY = "metadata"
    VECTOR_NAME = None

    @classmethod
    def construct_instance(
        cls: Type[Qdrant],
        texts: List[str],
        embedding: Embeddings,
        location: Optional[str] = None,
        url: Optional[str] = None,
        port: Optional[int] = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = False,
        https: Optional[bool] = None,
        api_key: Optional[str] = None,
        prefix: Optional[str] = None,
        timeout: Optional[float] = None,
        host: Optional[str] = None,
        path: Optional[str] = None,
        collection_name: Optional[str] = None,
        distance_func: str = "Cosine",
        content_payload_key: str = CONTENT_KEY,
        metadata_payload_key: str = METADATA_KEY,
        vector_name: Optional[str] = VECTOR_NAME,
        shard_number: Optional[int] = None,
        replication_factor: Optional[int] = None,
        write_consistency_factor: Optional[int] = None,
        on_disk_payload: Optional[bool] = None,
        hnsw_config: Optional[common_types.HnswConfigDiff] = None,
        optimizers_config: Optional[common_types.OptimizersConfigDiff] = None,
        wal_config: Optional[common_types.WalConfigDiff] = None,
        quantization_config: Optional[common_types.QuantizationConfig] = None,
        init_from: Optional[common_types.InitFrom] = None,
        on_disk: Optional[bool] = None,
        force_recreate: bool = False,
        **kwargs: Any,
    ) -> Qdrant:
        try:
            import qdrant_client  # noqa
        except ImportError:
            raise ValueError(
                "Could not import qdrant-client python package. "
                "Please install it with `pip install qdrant-client`."
            )
        from grpc import RpcError
        from qdrant_client.http import models as rest
        from qdrant_client.http.exceptions import UnexpectedResponse

        # Just do a single quick embedding to get vector size
        partial_embeddings = embedding.embed_documents(texts[:1])
        vector_size = len(partial_embeddings[0])
        collection_name = collection_name or uuid.uuid4().hex
        distance_func = distance_func.upper()
        custom_payload = kwargs.pop('payload', {})
        client, async_client = cls._generate_clients(
            location=location,
            url=url,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            https=https,
            api_key=api_key,
            prefix=prefix,
            timeout=timeout,
            host=host,
            path=path,
            **kwargs,
        )
        try:
            # Skip any validation in case of forced collection recreate.
            if force_recreate:
                raise ValueError

            # Get the vector configuration of the existing collection and vector, if it
            # was specified. If the old configuration does not match the current one,
            # an exception is being thrown.
            collection_info = client.get_collection(collection_name=collection_name)
            current_vector_config = collection_info.config.params.vectors
            if isinstance(current_vector_config, dict) and vector_name is not None:
                if vector_name not in current_vector_config:
                    raise QdrantException(
                        f"Existing Qdrant collection {collection_name} does not "
                        f"contain vector named {vector_name}. Did you mean one of the "
                        f"existing vectors: {', '.join(current_vector_config.keys())}? "
                        f"If you want to recreate the collection, set `force_recreate` "
                        f"parameter to `True`."
                    )
                current_vector_config = current_vector_config.get(vector_name)  # type: ignore[assignment]
            elif isinstance(current_vector_config, dict) and vector_name is None:
                raise QdrantException(
                    f"Existing Qdrant collection {collection_name} uses named vectors. "
                    f"If you want to reuse it, please set `vector_name` to any of the "
                    f"existing named vectors: "
                    f"{', '.join(current_vector_config.keys())}."  # noqa
                    f"If you want to recreate the collection, set `force_recreate` "
                    f"parameter to `True`."
                )
            elif (
                not isinstance(current_vector_config, dict) and vector_name is not None
            ):
                raise QdrantException(
                    f"Existing Qdrant collection {collection_name} doesn't use named "
                    f"vectors. If you want to reuse it, please set `vector_name` to "
                    f"`None`. If you want to recreate the collection, set "
                    f"`force_recreate` parameter to `True`."
                )

            # Check if the vector configuration has the same dimensionality.
            if current_vector_config.size != vector_size:  # type: ignore[union-attr]
                raise QdrantException(
                    f"Existing Qdrant collection is configured for vectors with "
                    f"{current_vector_config.size} "  # type: ignore[union-attr]
                    f"dimensions. Selected embeddings are {vector_size}-dimensional. "
                    f"If you want to recreate the collection, set `force_recreate` "
                    f"parameter to `True`."
                )

            current_distance_func = (
                current_vector_config.distance.name.upper()  # type: ignore[union-attr]
            )
            if current_distance_func != distance_func:
                raise QdrantException(
                    f"Existing Qdrant collection is configured for "
                    f"{current_distance_func} similarity, but requested "
                    f"{distance_func}. Please set `distance_func` parameter to "
                    f"`{current_distance_func}` if you want to reuse it. "
                    f"If you want to recreate the collection, set `force_recreate` "
                    f"parameter to `True`."
                )
        except (UnexpectedResponse, RpcError, ValueError):
            vectors_config = rest.VectorParams(
                size=vector_size,
                distance=rest.Distance[distance_func],
                on_disk=on_disk,
            )

            # If vector name was provided, we're going to use the named vectors feature
            # with just a single vector.
            if vector_name is not None:
                vectors_config = {  # type: ignore[assignment]
                    vector_name: vectors_config,
                }

            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                shard_number=shard_number,
                replication_factor=replication_factor,
                write_consistency_factor=write_consistency_factor,
                on_disk_payload=on_disk_payload,
                hnsw_config=hnsw_config,
                optimizers_config=optimizers_config,
                wal_config=wal_config,
                quantization_config=quantization_config,
                init_from=init_from,
                timeout=timeout,  # type: ignore[arg-type]
            )
        qdrant = cls(
            client=client,
            collection_name=collection_name,
            embeddings=embedding,
            content_payload_key=content_payload_key,
            metadata_payload_key=metadata_payload_key,
            distance_strategy=distance_func,
            vector_name=vector_name,
            async_client=async_client,
        )

        qdrant.payload = custom_payload
        return qdrant

    @classmethod
    def _build_payloads(
        cls,
        texts: Iterable[str],
        metadatas: Optional[List[dict]],
        content_payload_key: str,
        metadata_payload_key: str,
        custom_payload: Optional[Dict[Any, Any]]
    ) -> List[dict]:
        payloads = []
        for i, text in enumerate(texts):
            if text is None:
                raise ValueError(
                    "At least one of the texts is None. Please remove it before "
                    "calling .from_texts or .add_texts on Qdrant instance."
                )
            metadata = metadatas[i] if metadatas is not None else None
            payloads.append(
                {
                    content_payload_key: text,
                    metadata_payload_key: metadata,
                    **custom_payload
                }
            )
        return payloads
    
    def delete_prev_point(self, hash_id, collection_name):
        search_filter = Filter(
            must=[FieldCondition(
                key='hash_id',
                match=MatchValue(value=hash_id)
            )]
        )

        self.client.delete(
            collection_name=collection_name,
            points_selector=FilterSelector(
                filter=search_filter
            )
        )
 
    def is_file_uploaded(self, hash_id, collection):
        search_filter = Filter(
            must=[FieldCondition(
                key='hash_id',
                match=MatchValue(value=hash_id)
            )]
        )
        try:
            results = self.client.count(
                collection_name=collection,
                count_filter=search_filter,
                exact=True,
            )
        except UnexpectedResponse as e:
            return False
            
        return results.count > 0

    def generate_metadata_hash(self, country, category, file_name):
        hash_input = f"{country}_{category}_{file_name}".encode()
        return hashlib.sha256(hash_input).hexdigest()

    def _generate_rest_batches(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[Sequence[str]] = None,
        batch_size: int = 64,
    ) -> Generator[Tuple[List[str], List[rest.PointStruct]], None, None]:
        from qdrant_client.http import models as rest

        texts_iterator = iter(texts)
        metadatas_iterator = iter(metadatas or [])
        ids_iterator = iter(ids or [uuid.uuid4().hex for _ in iter(texts)])
        while batch_texts := list(islice(texts_iterator, batch_size)):
            # Take the corresponding metadata and id for each text in a batch
            batch_metadatas = list(islice(metadatas_iterator, batch_size)) or None
            batch_ids = list(islice(ids_iterator, batch_size))

            # Generate the embeddings for all the texts in a batch
            batch_embeddings = self._embed_texts(batch_texts)

            points = [
                rest.PointStruct(
                    id=point_id,
                    vector=vector
                    if self.vector_name is None
                    else {self.vector_name: vector},
                    payload=payload,
                )
                for point_id, vector, payload in zip(
                    batch_ids,
                    batch_embeddings,
                    self._build_payloads(
                        batch_texts,
                        batch_metadatas,
                        self.content_payload_key,
                        self.metadata_payload_key,
                        self.payload,
                    ),
                )
            ]

            yield batch_ids, points