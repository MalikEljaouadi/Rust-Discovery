use std::io;
use std::cmp::Ordering;
use rand::Rng;

fn main() {
    println!("Guess the number!");

    println!("input the number");
    
    let secret_number = rand::thread_rng().gen_range(1..101);
    
    let mut guess = String::new();
    io::stdin()
        .read_line(&mut guess)
        .expect("Error while reading input number");
    
    let guess:u32 = guess.trim().parse().expect("Unable to parse");

    println!("You guessed: {guess}");
    
    match guess.cmp(&secret_number){
        Ordering::Less => println!("too small"),
        Ordering::Equal => println!("equal"),
        Ordering::Greater => println!("too big"),
    }  
    println!("The secret_number is: {secret_number}");
}
