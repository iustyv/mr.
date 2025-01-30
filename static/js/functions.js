function toggleCardSelection(suit, rank) {
    const cardId = suit + rank;
    const cardElement = document.getElementById(cardId);

    if (selectedRank === null || selectedRank === rank) {
        selectedRank = rank;

        if (selectedCards.includes(cardId)) {
            selectedCards = selectedCards.filter(card => card !== cardId);
            cardElement.style.transform = "translateY(0px)";
        } else {
            selectedCards.push(cardId);
            cardElement.style.transform = "translateY(-20px)";
        }
    } else {
        resetCardSelection();
        selectedRank = rank;
        selectedCards.push(cardId);
        cardElement.style.transform = "translateY(-20px)";
    }

    document.getElementById("card").setAttribute("value", selectedCards.join(","));
}

function resetCardSelection() {
    selectedCards.forEach(cardId => {
        const cardElement = document.getElementById(cardId);
        if (cardElement) {
            cardElement.style.transform = "translateY(0px)";
        }
    });

    selectedCards = [];
    selectedRank = null;
}