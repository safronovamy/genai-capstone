from travelmate.services.rag_service import rebuild_index


def main():
    count = rebuild_index()
    print(f"Chroma index rebuilt successfully. Indexed documents: {count}")


if __name__ == "__main__":
    main()