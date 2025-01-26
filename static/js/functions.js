function selectCard(suit, rank) {
        const elements = document.querySelectorAll('.card');
        elements.forEach(element => {
            element.removeAttribute("style")
        });
        document.getElementById("card").setAttribute("value", suit + rank);
        document.getElementById(suit + rank).style.border = "2px solid red";
    }